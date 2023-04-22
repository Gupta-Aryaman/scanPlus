from flask import Flask, jsonify, request, abort, make_response
from flask_restful import Api, Resource
import json
import os
import bcrypt
# from flask_security import auth_required, logout_user, current_user
from functools import wraps

from models import *

from werkzeug.utils import secure_filename
import uuid as uuid

from htmlbody import *

from apscheduler.schedulers.background import BackgroundScheduler
import base64

from ner import *

import jwt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
import datetime


curr_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
# app.app_context()
# app.app_context().push()

# scheduler = APScheduler()
# scheduler.init_app(app)
# scheduler.start()
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
# scheduler.__init__(app)
scheduler.start()

# CORS(app, supports_credentials=True)
# app.config['CORS_HEADERS'] = 'Content-Type'
# app.secret_key = '38eyhdasjhy83e29qo8esdksan235e283ieqwiy2893'

# app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
# app.config['WTF_CSRF_ENABLED'] = False
# app.config['SECURITY_PASSWORD_SALT'] = 'dsaugdsanevwqydfbsa'

# app.config['SECRET_KEY'] = 'mysecretkey'
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this in your code!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

jwt = JWTManager(app)

api = Api(app)
# security = Security(app, user_datastore)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite"
# app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(os.getcwd(), 'database.sqlite')

upload_folder_pfp = "images/pfp"
app.config["UPLOAD_FOLDER_PFP"] = upload_folder_pfp

upload_folder_prescriptions = "images/prescriptions"
app.config["UPLOAD_FOLDER_prescriptions"] = upload_folder_prescriptions

db.init_app(app)
app.app_context().push()

salt = bcrypt.gensalt()


######################
from flask_mail import Mail, Message

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = '21f1003758@ds.study.iitm.ac.in',
    MAIL_PASSWORD = 'gtbvweccorelovqa',
))

mail= Mail(app)

def send_mail(message, mail_id):
    with app.app_context():
        msg = Message('Hello', sender = '21f1003758@ds.study.iitm.ac.in', recipients = [mail_id])
        # mail.send(msg)
        msg.html = mail_body(message)
        mail.send(msg)
        print("Sent")
        return

def encoding_image(path):
    with open(path, mode='rb') as file:
        img = file.read()
    return base64.b64encode(img).decode('utf-8')

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         if 'x-access-token' in request.headers:
#             token = request.headers['x-access-token']
#         if not token:
#             return jsonify({'message':'Token is missing!'})
#         # try:
#         #     print("HI")
#         #     data = jwt.decode(token, app.config['SECRET_KEY'])
#         #     print(data)
#         #     current_user = App_user.query.filter_by(email=data['email']).first()
#         # except:
#         #     return make_response("Invalid Token", 401, {'message': 'Token is invalid'})
#         data = get_jwt()["user"]
#         print(data['user'])
#         current_user = App_user.query.filter_by(email=data.encode('utf-8')).first()
#         print(current_user)
#         return f(current_user, *args, **kwargs)
    
#     return decorated

class SignUp(Resource):
    def post(self):
        fname = request.form['full_name']
        email = request.form['email'].encode('utf-8')
        pwd = request.form['password']
        isEmpty = App_user.query.filter_by(email = email).first()
        if isEmpty:
            return make_response("Invalid Email", 401, {'status': "exists"})

        pwd = bytes(pwd, 'utf-8')
        pwd = bcrypt.hashpw(pwd, salt)
        q = App_user(email = email, full_name = fname, password = pwd, profile_pic = "default_pic.png")
        db.session.add(q)
        db.session.commit()
        return make_response("User Successfully Registered",200, {'status' : "success"})
    

class Login(Resource):
    def post(self):
        email = request.form['email'].encode('utf-8')
        pwd = request.form['password'].encode('utf-8')
        find_user = App_user.query.filter_by(email = email).first()
        if find_user:
            user_pass = find_user.password
            if bcrypt.checkpw(pwd, user_pass):
                # token = jwt.encode({'user': str(find_user.email, 'UTF-8'), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                token = create_access_token(identity=str(find_user.email, 'UTF-8'))
                response = jsonify({"msg": "login successful"})
                set_access_cookies(response, token)
                print(token)
                return make_response("success", 200, {'authentication': "success", 'token': token})
            else:
                return make_response("Invalid Credentials", 401, {'authentication': "login required", 'token':''})
        else:
            return make_response("Invalid Credentials", 401, {'authentication': "login required", 'token':''})

class PrescriptionUpload(Resource):
    @jwt_required
    def post(self, current_user):
        try:
            email = current_user.email
            image = request.files['prescription']
            pic_filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename

            image.save(os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_name))

            q = Prescription(prescription_name = pic_name, user_email = email)
            db.session.add(q)
            db.session.commit()
            
            
            x = (ner_model.predict(detectText(os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_name))))

            medicine = x["Medicine"]
            msg = """Your Current Medication - 
            """
            counter = 0
            for i in medicine:
                msg = msg + str(counter) + ") " + i + "\n"

            job = scheduler.add_job(send_mail,'interval', [msg, email], hour = "10")

            return x

        except:
            abort(500)

class Dashboard(Resource):
    @jwt_required()
    def get(self):
        try:
        #uname = request.form["email"]
        # print(auth.current_user())
            email = get_jwt_identity().encode("utf-8")
            user = App_user.query.filter_by(email = email).first()
            uname = user.email
            # find_user = App_user.query.filter_by(email = uname).first()
            # if not find_user:
            #     abort(401)
            presciptions = Prescription.query.filter_by(user_email = uname).all()
            print(presciptions)
            presciptions_dict = {}
            for i in presciptions:
                temp = {}
                temp["id"] = i.id,
                temp["prescription_name"] =  i.prescription_name,
                temp["date"] = i.time_stamp.strftime('%m/%d/%Y'),
                print("./images/prescriptions/"+i.prescription_name)
                temp["image"] = encoding_image("./images/prescriptions/"+i.prescription_name),
                presciptions_dict[i.id] = temp
            print(presciptions_dict)
            return jsonify({"name": user.full_name, "pfp": user.profile_pic, "number_of_prescription": user.number_of_prescription, "prescriptions": presciptions_dict})
        except:
            abort(500)

class ViewPrescription(Resource):
    @jwt_required()
    def post(self):
        curr_id = request.form["id"]
        find_prescription = Prescription.query.filter_by(id = curr_id).first()
        if not find_prescription:
            abort(401)
        return make_response(jsonify({"picture":encoding_image("./images/prescriptions/"+find_prescription.prescription_name)}), 200)
        
class DeletePrescription(Resource):
    @jwt_required()
    def post(self):
        curr_id = request.form["id"]    
        x = Prescription.query.filter_by(id = curr_id).first()
        if not x:
            abort(401)
        db.session.delete(x)
        db.session.commit()
        return make_response(jsonify({'msg': "Successfully signed in!!!"}), 200)
    

class Logout(Resource): #done
    @jwt_required()
    def delete(self):
        response = jsonify({"msg": "logout successful"})
        unset_jwt_cookies(response)
        print(response)
        return response
        # logout_user()
        # return make_response(jsonify({'msg': "Successfully logged out!!!"}), 200)


class SendMail(Resource):
    def get(self):
        message = "hi"
        mail_id = "aryaman28112002@gmail.com"
        
        with app.app_context():
            job = scheduler.add_job(send_mail,'interval', ["hi", "aryaman28112002@gmail.com"], seconds=10)
        return

class Scan(Resource):
    def post(self):
        file_path = request.form['path']
        x = (ner_model.predict(detectText(file_path)))

        return json.dumps(x)

# @app.route("/")
# def test_func():
#     return "Hello World"

api.add_resource(Login, "/login")
api.add_resource(SignUp, "/signup")
api.add_resource(PrescriptionUpload, "/dashboard/upload_prescription")
api.add_resource(Dashboard, "/dashboard")
api.add_resource(ViewPrescription, "/dashboard/view")
api.add_resource(DeletePrescription, "/dashboard/delete")
api.add_resource(Logout, "/logout")
api.add_resource(SendMail, "/api/mail")
api.add_resource(Scan, "/scan")

if __name__=="__main__":
    db.create_all()
    
    ner_model = initiate_ner()
    ner_model.load_model("/home/aryaman/Desktop/raj-it/content/model")
    app.run(debug=True)