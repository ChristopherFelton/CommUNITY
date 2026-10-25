from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from math import isfinite
from datetime import datetime, timedelta
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

from models import Opportunity,User,Signup

with app.app_context():
    db.create_all()

def searchBar(query, oppList):
    results = []

    for i in range(len(oppList)):
        if query.lower() in oppList[i].title.lower() or query.lower() in oppList[i].poster.lower():
            results.append(oppList[i])

    return results

def sortByTime(oppList):
    sortedList = []
    indexList = []
    timeList = []

    for i in range(len(oppList)):
        timeDifference = oppList[i].date - datetime.now()
        if timeDifference>timedelta(0):
            timeList.append(timeDifference)
        else:
            timeList.append(None)
        indexList.append(i)

    for i in range(len(timeList)):
        for j in range(len(timeList)-i):
            if timeList[indexList[i:len(indexList)][j]] != None:
                if timeList[indexList[i]] == None or timeList[indexList[i]] > timeList[indexList[i:len(indexList)][j]]:
                    n = indexList[j+i]
                    del indexList[j+i]
                    indexList.insert(i, n)

    for i in range(len(oppList)):
        if timeList[indexList[i]] != None:
            sortedList.append(oppList[indexList[i]])

    return sortedList

def sortByDistance(user, radius, oppList):
    sortedList = []
    oppDist = []
    indexList = []
    userCoord = (user.latitude, user.longitude)

    for i in range(len(oppList)):
        distance = geodesic(userCoord, (oppList[i].latitude, oppList[i].longitude)).miles
        indexList.append(i)
        if datetime.now() < oppList[i].date and oppList[i].capacity > 0:
            if(radius>0):
                if(distance <= radius):
                    oppDist.append(distance)
                else:
                    oppDist.append(None)
            else:
                oppDist.append(distance)
        else:
            oppDist.append(None)

    for i in range(len(oppDist)):
        for j in range(len(oppDist)-i):
            if oppDist[indexList[i:len(indexList)][j]] != None:
                if oppDist[indexList[i]] == None or oppDist[indexList[i]] > oppDist[indexList[i:len(indexList)][j]]:
                    n = indexList[j+i]
                    del indexList[j+i]
                    indexList.insert(i, n)

    for i in range(len(oppList)):
        if(oppDist[indexList[i]] != None):
            sortedList.append(oppList[indexList[i]])

    return sortedList

def sortBySkill(skillList, oppList):
    sortedList = []
    indexList = []
    recSkillsList = []  #a list of skills recommended by the opportunity of the same index

    for i in range(len(oppList)):
        recSkillsList.append(oppList[i].skills.split(", "))
        indexList.append(i)

    countList = [0] * len(recSkillsList)

    for i in range(len(skillList)):
        for j in range(len(recSkillsList)):
            for k in range(len(recSkillsList[j])):
                if recSkillsList[j][k] == skillList[i]:
                    countList[j] += 1
                    break

    n = 0
    for i in range(len(countList)):
        for j in range(len(countList)-i):
            if countList[indexList[i:len(indexList)][j]] > countList[indexList[i]]:
                n = indexList[j+i]
                del indexList[j+i]
                indexList.insert(i, n)

    for i in range(len(indexList)):
        sortedList.append(oppList[indexList[i]])

    return sortedList

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/opportunities",methods=["GET","POST"])
def opportunities():
    all_opportunities = Opportunity.query.all()
    #if we're not signed in
    if session.get("username") is None:
        flash("Please sign in to browse opportunities.")
        return redirect(url_for("home"))
    #if we're not a volunteer
    user = db.session.get(User, session["username"])
    if user is None:
        session.clear()
        flash("Your session has expired. Please sign in again.")
        return redirect(url_for("login"))
    if not user.volunteer:
        flash("Opportunity browsing is only available to volunteers.")
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
        keyword_results = (
            searchBar(query, all_opportunities)
            if query
            else all_opportunities
        )
        distance_results = sortByDistance(user, int(radius), keyword_results)

        if selected_skills:
            selected_skill_set = set(selected_skills)
            filtered_opportunities = [
                opportunity
                for opportunity in distance_results
                if selected_skill_set.intersection(
                    skill.strip() for skill in opportunity.skills.split(",")
                )
            ]
        else:
            filtered_opportunities = distance_results

        bestArr = sortBySkill(selected_skills, filtered_opportunities)
        timeArr = sortByTime(filtered_opportunities)
        if(sort_by == "nearest"):
            return render_template(
                "opportunities.html",
                opportunities=filtered_opportunities,
            )
        if(sort_by == "best"):
            return render_template("opportunities.html",opportunities=bestArr)
        if(sort_by == "soonest"):
            return render_template("opportunities.html",opportunities=timeArr)
   
    available_opportunities = [
        opportunity
        for opportunity in all_opportunities
        if opportunity.date > datetime.now() and opportunity.capacity > 0
    ]
    userSkills = user.skills
    profile_skills = userSkills.split(", ") if userSkills else []
    if userSkills == "":
        return render_template(
            "opportunities.html",
            opportunities=available_opportunities,
            profile_skills=profile_skills,
        )
    else:
        userSkills=userSkills.split(", ")
        bestArr = sortBySkill(userSkills, available_opportunities)
        return render_template(
            "opportunities.html",
            opportunities=bestArr,
            profile_skills=profile_skills,
        )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if username == None:
        flash("Please sign in to view your dashboard.")
        return redirect(url_for("login"))
    user = db.session.get(User, username)
    if user is None:
        session.clear()
        flash("Your session has expired. Please sign in again.")
        return redirect(url_for("login"))
    if not user.volunteer:
        flash("The volunteer dashboard is only available to volunteers.")
        return redirect(url_for("organization_dashboard"))
    signed_up_opportunities = (Opportunity.query.join(Signup, Signup.opportunity_id == Opportunity.id).filter(Signup.volunteer_username == username).all())
    return render_template("dashboard.html",user=user,signups=signed_up_opportunities,)

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
            flash("Incorrect username or password.")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first() is not None:
            flash("That username is already taken. Please choose another.")
            return redirect(url_for("signup"))
        if request.form.get("volunteer") == "yes":
            volunteer = True
            name = request.form.get("name")
            selected_skills = ", ".join(
                skill for skill in SKILLS
                if skill in request.form.getlist("skills")
            )
            latitude = request.form.get("latitude", type=float)
            longitude = request.form.get("longitude", type=float)
            if (
                latitude is None
                or longitude is None
                or not isfinite(latitude)
                or not isfinite(longitude)
                or not -90 <= latitude <= 90
                or not -180 <= longitude <= 180
            ):
                flash("Please enter a valid U.S. ZIP code so we can find your location.")
                return redirect(url_for("signup"))
        else:
            volunteer = False
            name = ""
            selected_skills = ""
            latitude = None
            longitude = None
        new_user = User(
            username=username,
            hours=0,
            skills=selected_skills,
            password=password,
            volunteer=volunteer,
            opportunity_id="",
            name = name,
            latitude=latitude,
            longitude=longitude,
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
        flash("Please sign in to view the organization dashboard.")
        return redirect(url_for("home"))
    username = session.get("username")
    if username is None:
        flash("Please sign in to view the organization dashboard.")
        return redirect(url_for("login"))

    user = db.session.get(User, username)
    if user is None:
        session.clear()
        flash("Your session has expired. Please sign in again.")
        return redirect(url_for("login"))
    if user.volunteer:
        flash("The organization dashboard is only available to organizations.")
        return redirect(url_for("opportunities"))

    if request.method == "POST":
        latitude = request.form.get("latitude", type=float)
        longitude = request.form.get("longitude", type=float)
        if (
            latitude is None
            or longitude is None
            or not isfinite(latitude)
            or not isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            flash("Please select a valid event location on the map.")
            return redirect(url_for("organization_dashboard"))

        new_opportunity = Opportunity(
            title=request.form["title"],
            date=datetime.strptime(request.form["date"], "%Y-%m-%d"),
            description=request.form["description"],
            location=request.form["location"],
            skills=request.form["skills"],
            capacity=int(request.form["capacity"]),
            poster=username,
            latitude=latitude,
            longitude=longitude,
        )
        db.session.add(new_opportunity)
        db.session.commit()
        return redirect(url_for("organization_dashboard"))

    my_opportunities = Opportunity.query.filter_by(poster=username).all()
    return render_template(
        "organization_dashboard.html",
        opportunities=my_opportunities
    )

@app.route("/opportunities/<int:opportunity_id>")
def opportunity_detail(opportunity_id):
    opportunity = db.get_or_404(Opportunity, opportunity_id)
    return render_template("opportunity_detail.html",opportunity=opportunity)

@app.route("/opportunities/<int:opportunity_id>/add",methods=["POST"])
def add(opportunity_id):
    if session.get("username") is None:
        flash("Please sign in before registering for an opportunity.")
        return redirect(url_for("home"))
    user = db.session.get(User, session["username"])
    if user is None:
        session.clear()
        flash("Your session has expired. Please sign in again.")
        return redirect(url_for("login"))
    if not user.volunteer:
        flash("Only volunteers can register for opportunities.")
        return redirect(url_for("organization_dashboard"))
    opportunity = db.session.get(Opportunity, opportunity_id)
    if opportunity is None:
        flash("That opportunity could not be found.")
        return redirect(url_for("opportunities"))
    if Signup.query.filter_by(
        volunteer_username=user.username,
        opportunity_id=opportunity_id,
    ).first() is not None:
        flash("You're already registered for this event.")
        return redirect(url_for("opportunity_detail", opportunity_id=opportunity_id))
    newSignup = Signup(volunteer_username=session["username"],opportunity_id=opportunity_id)
    db.session.add(newSignup)

    db.session.commit()
    return redirect(url_for("opportunity_detail",opportunity_id=opportunity_id))

@app.route("/opportunities/<int:opportunity_id>/unregister", methods=["POST"])
def unregister(opportunity_id):
    username = session.get("username")
    if username is None:
        flash("Please sign in to unregister from an opportunity.")
        return redirect(url_for("login"))

    user = db.session.get(User, username)
    if user is None:
        session.clear()
        flash("Your session has expired. Please sign in again.")
        return redirect(url_for("login"))
    if not user.volunteer:
        flash("Only volunteers can unregister from opportunities.")
        return redirect(url_for("organization_dashboard"))

    signup = Signup.query.filter_by(
        volunteer_username=username,
        opportunity_id=opportunity_id,
    ).first()
    if signup is None:
        flash("You aren't registered for that opportunity.")
        return redirect(url_for("dashboard"))

    db.session.delete(signup)
    db.session.commit()
    flash("You have been unregistered from the opportunity.")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)