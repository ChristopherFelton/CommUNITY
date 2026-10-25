from extensions import db
class Opportunity(db.Model):
    __tablename__ = "opportunities"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    poster = db.Column(db.Text,nullable=True)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)

class User(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(16),primary_key=True)
    hours = db.Column(db.Float, nullable = False)
    skills = db.Column(db.Text,nullable=False)
    password = db.Column(db.Text,nullable=False)
    volunteer = db.Column(db.Boolean,nullable=False)
    opportunity_id = db.Column(db.Text,nullable=False)
    name = db.Column(db.Text,nullable=True)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)