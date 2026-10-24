from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text
from extensions import db

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

db.init_app(app)

from models import Opportunity,User

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/opportunities")
def opportunities():
    all_opportunities = Opportunity.query.all()
    userSkills = User.query.filter_by(username=session["username"]).first().skills
    if userSkills == "":
        userSkills = []
    else:
        userSkills=userSkills.split(",")
    print(userSkills)
    return render_template(
        "opportunities.html",
        opportunities=all_opportunities
    )

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
        opportunity_ids = db.session.query(Opportunity.id).all()
        existing_numbers = [
            int(opportunity_id.removeprefix("CS-"))
            for (opportunity_id,) in opportunity_ids
            if opportunity_id.startswith("CS-")
            and opportunity_id.removeprefix("CS-").isdigit()
        ]
        opportunity_id = f"CS-{max(existing_numbers, default=0) + 1}"

        new_opportunity = Opportunity(
            id=opportunity_id,
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