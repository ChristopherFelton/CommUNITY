from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text
from extensions import db
from geopy.distance import geodesic

SKILLS = (
    "Animal Care",
    "Childcare",
    "Communication",
    "Compassion",
    "Customer Service",
    "Environmental Care",
    "Environmental Knowledge",
    "Event Coordination",
    "Food Preparation",
    "Gardening",
    "Hospitality",
    "Leadership",
    "Manual Labor",
    "Organization",
    "Patience",
    "Physical Agility",
    "Physical Lifting",
    "Public Speaking",
    "Sanitation",
    "Sorting",
    "Teaching",
    "Teamwork",
    "Tech Savviness",
    "Tutoring",
)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["GOOGLE_MAPS_API_KEY"] = os.environ.get("GOOGLE_MAPS_API_KEY", "")

db.init_app(app)

from models import Opportunity,User

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/opportunities",methods=["GET","POST"])
def opportunities():
    #if we're not signed in
    if session.get("username") is None:
        return redirect(url_for("home"))
    #if we're not a volunteer
    if User.query.filter_by(username=session["username"]).first().volunteer == False:
        return redirect(url_for("organization_dashboard"))

    if request.method == "POST":
        #search text
        query = request.form.get("q", "").strip()
        #skills required
        selected_skills = request.form.getlist("skills")
        #whether to sort by best match,nearest,soonest
        sort_by = request.form.get("sort", "best")
        #biggest acceptable radius
        radius = request.form.get("radius", "10")

    all_opportunities = Opportunity.query.all()
    userSkills = User.query.filter_by(username=session["username"]).first().skills
    if userSkills == "":
        userSkills = []
    else:
        userSkills=userSkills.split(",")
    print(userSkills)
    return render_template("opportunities.html",opportunities=all_opportunities)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if username == None:
        return redirect(url_for("login"))
    user = db.session.get(User, username)
    if not user.volunteer:
        return redirect(url_for("organization_dashboard"))
    #signups=[] needs to become the opportunities_id with all the events they signed up for later
    return render_template("dashboard.html",user=user,signup=[])

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.session.get(User,username)
        if user and password == user.password:
            session.clear()
            session["username"] = user.username
            if user.volunteer:
                return redirect(url_for("opportunities"))
            else:
                return redirect(url_for("organization_dashboard"))
        else:
            print("bad username or password")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if request.form.get("volunteer") == "yes":
            volunteer = True
            name = request.form.get("name")
            selected_skills = ", ".join(
                skill for skill in SKILLS
                if skill in request.form.getlist("skills")
            )
        else:
            volunteer = False
            name = ""
            selected_skills = ""
        new_user = User(
            username=username,
            hours=0,
            skills=selected_skills,
            password=password,
            volunteer=volunteer,
            opportunity_id="",
            name = name
        )
        db.session.add(new_user)
        db.session.commit()
        session.clear()
        session["username"] = username
        if volunteer:
            return redirect(url_for("opportunities"))
        else:
            return redirect(url_for("organization_dashboard"))
    return render_template("signup.html", skills=SKILLS)

@app.route("/organization_dashboard",methods=["GET","POST"])
def organization_dashboard():
    if session.get("username") is None:
        return redirect(url_for("home"))
    if User.query.filter_by(username=session["username"]).first().volunteer:
        all_opportunities = Opportunity.query.all()
        return redirect(url_for("opportunities",opportunities=all_opportunities))
    username = session.get("username")
    if username is None:
        return redirect(url_for("login"))

    user = db.session.get(User, username)
    if user is None:
        session.clear()
        return redirect(url_for("login"))
    if user.volunteer:
        return redirect(url_for("opportunities"))

    if request.method == "POST":
        new_opportunity = Opportunity(
            title=request.form["title"],
            date=datetime.strptime(request.form["date"], "%Y-%m-%d"),
            description=request.form["description"],
            location=request.form["location"],
            skills=request.form["skills"],
            capacity=int(request.form["capacity"]),
            poster=username,
        )
        db.session.add(new_opportunity)
        db.session.commit()
        return redirect(url_for("organization_dashboard"))

    my_opportunities = Opportunity.query.filter_by(poster=username).all()
    return render_template(
        "organization_dashboard.html",
        opportunities=my_opportunities
    )

if __name__ == "__main__":
    app.run(debug=True)

def sortByDistance(user):
    sortedList = []
    oppList = Opportunity.query.all()
    oppDist = []
    indexList = []
    userCoord = (user.longitude, user.latitude)

    for i in range(len(oppList)):
        indexList.append(i)
        oppDist.append(geodisc(userCoord, (oppList[i].longitude, oppList[i].latitude)).miles)

    i = 0
    n = 0
    while i < len(oppList):
        for j in range(len(oppList)):
            if oppDist[j] < oppDist[i]:
                n = indexList[i]
                indexList[i] = indexList[j]
                indexList[j] = n
                i += 1
                break

            i += 1

    for i in range(len(oppList)):
        sortedList.append(oppList[indexList[i]])

    return sortedList 

def sortBySkill(skillList, oppList):
    sortedList = []
    indexList = []
    recSkillsList = []  #a list of skills recommended by the opportunity of the same index
    maxCount = 0

    for i in range(len(oppList)):
        recSkillsList.append(oppList[i].get_skills().split(", "))
        indexList.append(i)

    countList = [0] * len(recSkillsList)

    for i in range(len(skillList)):
        for j in range(len(recSkillsList)):
            for k in range(len(recSkillsList[j])):
                if recSkillsList[j][k] == skillList[i]:
                    countList[j] += 1
                    if maxCount < countList[j]:
                        maxCount = countList[j]
                    break

    n = 0
    for i in range(maxCount, 0, -1):
        for j in range(len(countList)):
            if countList[indexList[j]] == i:
                n = indexList[j]
                del indexList[j]
                indexList.insert(0, n)

    for i in range(len(indexList)):
        sortedList.append(oppList[indexList[i]])

    sortedList.reverse()
    return sortedList

