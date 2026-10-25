from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import or_, text
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
app.config["GOOGLE_MAPS_API_KEY"] = os.environ.get("GOOGLE_MAPS_API_KEY", "")

db.init_app(app)

from models import Opportunity,User

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/opportunities")
def opportunities():
    search_query = request.args.get("q", "").strip()
    sort = request.args.get("sort", "best")
    if sort not in {"best", "nearest", "soonest"}:
        sort = "best"

    username = session.get("username")
    user = db.session.get(User, username) if username else None
    if user is not None and not user.volunteer:
        user = None
    has_location = bool(
        user and user.latitude is not None and user.longitude is not None
    )

    if "filters" in request.args:
        selected_skills = [
            skill for skill in request.args.getlist("skills")
            if skill in SKILLS
        ]
    elif user and user.skills:
        selected_skills = [
            skill.strip() for skill in user.skills.split(",")
            if skill.strip() in SKILLS
        ]
    else:
        selected_skills = []

    radius_options = {"0", "5", "10", "25", "50"}
    radius = request.args.get("radius", "0")
    if radius not in radius_options:
        radius = "0"
    if not has_location:
        radius = "0"

    query = Opportunity.query
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(or_(
            Opportunity.title.ilike(search_pattern),
            Opportunity.description.ilike(search_pattern),
            Opportunity.location.ilike(search_pattern),
            Opportunity.poster.ilike(search_pattern),
        ))

    selected_skill_set = {skill.casefold() for skill in selected_skills}
    opportunities_with_match = []
    for opportunity in query.all():
        opportunity_skills = {
            skill.strip().casefold()
            for skill in (opportunity.skills or "").split(",")
            if skill.strip()
        }
        matching_skills = selected_skill_set & opportunity_skills

        if selected_skill_set and not matching_skills:
            continue

        distance_miles = None
        if (
            user
            and user.latitude is not None
            and user.longitude is not None
            and opportunity.latitude is not None
            and opportunity.longitude is not None
        ):
            latitude_delta = radians(opportunity.latitude - user.latitude)
            longitude_delta = radians(opportunity.longitude - user.longitude)
            haversine = (
                sin(latitude_delta / 2) ** 2
                + cos(radians(user.latitude))
                * cos(radians(opportunity.latitude))
                * sin(longitude_delta / 2) ** 2
            )
            distance_miles = (
                3958.8 * 2 * asin(sqrt(min(1, haversine)))
            )

        if radius != "0":
            if distance_miles is None or distance_miles > int(radius):
                continue

        opportunities_with_match.append({
            "opportunity": opportunity,
            "matching_skill_count": len(matching_skills),
            "matching_skills": matching_skills,
            "distance_miles": distance_miles,
        })

    if sort == "nearest":
        opportunities_with_match.sort(
            key=lambda item: (
                item["distance_miles"] is None,
                item["distance_miles"] if item["distance_miles"] is not None else 0,
                item["opportunity"].date,
            )
        )
    elif sort == "soonest":
        opportunities_with_match.sort(
            key=lambda item: item["opportunity"].date
        )
    else:
        opportunities_with_match.sort(
            key=lambda item: (
                -item["matching_skill_count"],
                item["opportunity"].date,
            )
        )

    return render_template(
        "opportunities.html",
        opportunities=opportunities_with_match,
        search_query=search_query,
        sort=sort,
        skills=SKILLS,
        selected_skills=selected_skills,
        radius=radius,
        has_location=has_location,
    )

@app.route("/opportunities/<int:opportunity_id>")
def opportunity_detail(opportunity_id):
    # Read-only for now. The detail page also has an "Add to my list" form that posts to
    # /opportunities/<id>/add; that route doesn't exist yet (the backend must add it, and pass
    # org_name, spots_left, in_list, and the other optional fields the template reads).
    opportunity = db.get_or_404(Opportunity, opportunity_id)
    return render_template("opportunity_detail.html", opportunity=opportunity)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if username is None:
        return redirect(url_for("login"))

    user = db.session.get(User, username)
    if user is None:
        session.clear()
        return redirect(url_for("login"))
    if not user.volunteer:
        return redirect(url_for("organization_dashboard"))

    opportunity_ids = []
    for value in (user.opportunity_id or "").split(","):
        value = value.strip()
        if value.isdigit():
            opportunity_ids.append(int(value))

    if opportunity_ids:
        signups = (
            Opportunity.query
            .filter(Opportunity.id.in_(opportunity_ids))
            .order_by(Opportunity.date)
            .all()
        )
    else:
        signups = []

    return render_template("dashboard.html", user=user, signups=signups)

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
            # The login page shows flashed messages.
            flash("Invalid username or password.")
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
            try:
                latitude = float(request.form["latitude"])
                longitude = float(request.form["longitude"])
            except (KeyError, ValueError):
                return render_template(
                    "signup.html",
                    skills=SKILLS,
                    error="We couldn't determine coordinates from that ZIP code. Please try again.",
                ), 400

            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return render_template(
                    "signup.html",
                    skills=SKILLS,
                    error="The location lookup returned invalid coordinates. Please try again.",
                ), 400

            selected_skills = ", ".join(
                skill for skill in SKILLS
                if skill in request.form.getlist("skills")
            )
        else:
            volunteer = False
            name = ""
            latitude = None
            longitude = None
            selected_skills = ""
        new_user = User(
            username=username,
            hours=0,
            skills=selected_skills,
            password=password,
            volunteer=volunteer,
            opportunity_id="",
            name=name,
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
            longitude=request.form["longitude"],
            latitude=request.form["latitude"]
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
    # Port 5000 is taken on this Mac (AirPlay Receiver), so run on 5001.
    app.run(debug=True, port=5001)