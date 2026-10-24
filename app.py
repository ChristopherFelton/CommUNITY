from flask import Flask, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text
from extensions import db

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

db.init_app(app)

from models import Opportunity,Volunteer

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/opportunities")
def opportunities():
    all_opportunities = Opportunity.query.all()
    return render_template(
        "opportunities.html",
        opportunities=all_opportunities
    )
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)