from web_api_base import app
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Models (re-using the previously defined classes)


class UserInfo(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(255))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    allergic = db.Column(db.String(255))
    body_fat = db.Column(db.String(50))
    hometown = db.Column(db.String(255))
    goal = db.Column(db.String(255))
    love_foods = db.Column(db.String(255))


class Recommendations(db.Model):
    recommendation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_info.user_id'))
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.String(1000))
    based_on_habits = db.Column(db.Boolean)
    based_on_function_facts = db.Column(db.Boolean)
    rank = db.Column(db.Integer)
    rate = db.Column(db.Integer)
    save = db.Column(db.Boolean)

