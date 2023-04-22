from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, SQLAlchemyUserDatastore
from datetime import datetime, timedelta

db = SQLAlchemy()

class App_user(db.Model, UserMixin):
    __tablename__ = 'app_user'
    id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    email = db.Column(db.String, nullable = False, unique = True)
    full_name = db.Column(db.String, nullable = False)
    # last_name = db.Column(db.String, nullable = False)
    profile_pic = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
    number_of_prescription = db.Column(db.Integer, nullable = False, default = 0)
    # active = db.Column(db.Boolean())
    # fs_uniquifier = db.Column(db.String(255), nullable = False, unique = True)
    # def get_security_payload(self):
    #     return {"id":self.id}

user_datastore = SQLAlchemyUserDatastore(db, App_user, None)

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    prescription_name =  db.Column(db.String, nullable = False)
    user_email = db.Column(db.String, nullable = False)
    time_stamp = db.Column(db.DateTime, default = datetime.utcnow)