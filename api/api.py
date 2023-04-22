from flask import Flask, jsonify, request, abort
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import os
import bcrypt
from datetime import datetime
from flask_httpauth import HTTPBasicAuth

#for picture
from werkzeug.utils import secure_filename
import uuid as uuid

from PIL import Image #module name = pillow


curr_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"

upload_folder_pfp = "images/pfp"
app.config["UPLOAD_FOLDER_PFP"] = upload_folder_pfp

upload_folder_prescriptions = "images/prescriptions"
app.config["UPLOAD_FOLDER_prescriptions"] = upload_folder_prescriptions

db = SQLAlchemy(app)
app.app_context().push()

auth = HTTPBasicAuth()

salt = bcrypt.gensalt()

class App_user(db.Model):
    __tablename__ = 'app_user'
    id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    email = db.Column(db.String, nullable = False, unique = True)
    full_name = db.Column(db.String, nullable = False)
    # last_name = db.Column(db.String, nullable = False)
    profile_pic = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)
    number_of_prescription = db.Column(db.Integer, nullable = False, default = 0)

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    prescription_name =  db.Column(db.String, nullable = False)
    user_email = db.Column(db.String, nullable = False)
    time_stamp = db.Column(db.DateTime, default = datetime.utcnow)

class SignUp(Resource):
    def post(self):
        # try:
        fname = request.form['full_name']
        email = request.form['email']
        pwd = request.form['pwd']
        # pic = request.files['pfp']
        isEmpty = App_user.query.filter_by(email = email).first()

        if isEmpty:
            abort(401)

        # pic_filename = secure_filename(pic.filename)
        # pic_name = str(uuid.uuid1()) + "_" + pic_filename

        # pic.save(os.path.join(app.config['UPLOAD_FOLDER_PFP'], pic_name))

        pwd = bytes(pwd, 'utf-8')
        pwd = bcrypt.hashpw(pwd, salt)
        try:
            q = App_user(email = email, full_name = fname, password = pwd, profile_pic = "default_pic.png")
            db.session.add(q)
            db.session.commit()
            return "SUCCESS"
        except:
            abort(500)

@auth.verify_password
def verify_password(uname, pwd):
    find_user = App_user.query.filter_by(email = uname).first()
    if find_user:
        user_pass = find_user.password
        if bcrypt.checkpw(pwd.encode('utf8'), user_pass):
            return find_user

class Login(Resource):
    def post(self):
        uname = request.form["email"]
        pwd = request.form["pwd"]

        if verify_password(uname, pwd) == None:
            abort(401)
        else:
            return "SUCCESS"


class PrescriptionUpload(Resource):
    @auth.login_required
    def post(self):
        try:
            email = auth.current_user().email
            # image = request.files['prescription']
            # pic_filename = secure_filename(image.filename)
            # pic_name = str(uuid.uuid1()) + "_" + pic_filename

            # image.save(os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_name))

            q = Prescription(prescription_name = "pic_name", user_email = email)
            db.session.add(q)
            db.session.commit()
            return "SUCCESS"
        except:
            abort(500)

class Dashboard(Resource):
    @auth.login_required
    def get(self):
        try:
        #uname = request.form["email"]
        # print(auth.current_user())
            user = auth.current_user()
            uname = user.email
            # find_user = App_user.query.filter_by(email = uname).first()
            # if not find_user:
            #     abort(401)
            presciptions = Prescription.query.filter_by(user_email = uname).all()
            presciptions_dict = {}
            for i in presciptions:
                presciptions_dict[i.id] = {i.prescription_name: i.time_stamp.strftime('%m/%d/%Y')}
            print(presciptions_dict)
            return jsonify({"name": user.full_name, "pfp": user.profile_pic, "number_of_prescription": user.number_of_prescription, "prescriptions": presciptions_dict})
        except:
            abort(500)

class ViewPrescription(Resource):
    @auth.login_required
    def post(self):
        curr_id = request.form["id"]
        find_prescription = Prescription.query.filter_by(id = curr_id).first()
        if not find_prescription:
            abort(401)
        return find_prescription.prescription_name

class DeletePrescription(Resource):
    @auth.login_required
    def post(self):
        curr_id = request.form["id"]
        x = Prescription.query.filter_by(id = curr_id).first()
        if not x:
            abort(401)
        db.session.delete(x)
        db.session.commit()
        return "SUCCESS"


class Logout(Resource):
    @auth.login_required
    def get(self):
        return "Logout", 401
    
api.add_resource(SignUp, "/signup")
api.add_resource(Login, "/login")
api.add_resource(PrescriptionUpload, "/dashboard/upload_prescription")
api.add_resource(Dashboard, "/dashboard")
api.add_resource(ViewPrescription, "/dashboard/view")
api.add_resource(DeletePrescription, "/dashboard/delete")
api.add_resource(Logout, "/logout")


if __name__=="__main__":
    db.create_all()
    app.run(debug=True)