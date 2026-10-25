from flask import Flask, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)
@app.route("/")
def home():
    return render_template("index.html")

# Sign up page, GET only for now. The backend teammate owns this route and must add
# POST handling (validate the form, hash the password, save the user) before sign up works.
@app.route("/signup")
def signup():
    return render_template("signup.html")

# Log in page, GET only for now. The backend teammate owns this route and must add
# POST handling (check the username and password, start the session, flash() an error if wrong).
@app.route("/login")
def login():
    return render_template("login.html")

# Dashboard (the signed-in user's home page), GET only for now. The backend teammate owns this
# route and must require login and pass real data: user, signups, hours_completed, hours_goal.
# Until then the template shows clearly labeled sample data.
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Organization dashboard, GET only for now. The backend teammate owns this route and must require
# an organization login and pass real data: org, upcoming_events, past_events.
# Until then the template shows clearly labeled sample data.
@app.route("/org/dashboard")
def org_dashboard():
    return render_template("org_dashboard.html")

# Create-event page, GET only for now. The backend teammate owns this route and must require an
# organization login and add POST handling (validate the form, save the opportunity, flash() errors).
@app.route("/opportunities/create")
def create_opportunity():
    return render_template("create_opportunity.html")

# Volunteer onboarding questionnaire, GET only for now. The backend teammate owns this route and
# must require login, handle the POST (save the answers for matching), and redirect new volunteers
# here right after sign-up. It may pass skill_options, interest_options, and answers (to prefill).
@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

# Opportunities matched to the volunteer's answers, GET only. The backend teammate owns this route
# and must require login and pass real data: opportunities and answers. It must also do the matching,
# ranking, and sorting itself, using the query parameters (q, sort, the edited answers, save_answers).
# Until then the template shows clearly labeled sample data.
@app.route("/opportunities")
def opportunities():
    return render_template("opportunities.html")

# Opportunity detail page, GET only for now. The backend teammate owns this route and must pass the
# real opportunity (look it up by opportunity_id, 404 if missing, and set in_list for the signed-in
# student), and must also add POST /opportunities/<id>/add (put the event on the student's dashboard).
# Until then the template shows clearly labeled sample data.
@app.route("/opportunities/<int:opportunity_id>")
def opportunity_detail(opportunity_id):
    return render_template("opportunity_detail.html")



if __name__ == "__main__":
    app.run(debug=True)
