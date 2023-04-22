from flask import Flask, render_template, request, redirect
import requests
from werkzeug.utils import secure_filename
import uuid
import os
import ast

app = Flask(__name__)

app.config['token'] = ""
app.config['email'] = ""
app.config['UPLOAD_FOLDER_SCAN'] = "/home/aryaman/Desktop/main-app/static/temp"
upload_folder_prescriptions = "/home/aryaman/Desktop/raj-it/images/prescriptions"
app.config["UPLOAD_FOLDER_prescriptions"] = upload_folder_prescriptions


api_url = "http://127.0.0.1:5000"

@app.route("/", methods = ["GET"])
def home_page():
    return render_template("home.html")

@app.route("/about", methods = ["GET"])
def about():
    return render_template("about.html")

@app.route("/contact", methods = ["GET"])
def contact():
    return render_template("contact.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method=="POST":
        data = {}
        data['email'] = request.form['email']
        data['password'] = request.form['password']

        response = requests.post(
            api_url + '/login',
            data
        )
        if response.headers['authentication']=="success":
            app.config['token'] = response.headers['token']
            app.config['email'] = data['email']
            print(app.config['token'])
            return redirect("/dashboard")
        else:
            return redirect("/login?status=invalid")

    else:
        status = request.args.get('status')
        return render_template("login.html", status=status)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = {}
        data['full_name'] = request.form['name']
        data['email'] = request.form['email']
        data['password'] = request.form['password']
        
        response = requests.post(
            api_url + '/signup',
            data
            )
        if response.headers['status']=="exists":
            return redirect("/signup?status=invalid")
        return redirect("/login?status=success")
    else:
        status = request.args.get('status')
        print(status)
        return render_template("signup.html", status=status)
    
@app.route("/scan", methods = ["GET", "POST"])
def scan():
    if request.method =="POST":
        pic = request.files['picture']
        pic_filename = secure_filename(pic.filename)
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        pic.save(os.path.join(app.config['UPLOAD_FOLDER_SCAN'], pic_name))
        
        data = {'path': os.path.join(app.config['UPLOAD_FOLDER_SCAN'], pic_name)}

        response = requests.post(
            api_url + '/scan',
            data
            ).json()
        
        response = ast.literal_eval(response)

        medicines_list = []
        if "Medicine" in response and "Frequency" in response:
            len_of_medicine = len(response['Medicine'])
            len_of_freq = len(response['Frequency'])
            i = 0
            j = 0
            while i<len_of_medicine and j<len_of_freq:
                medicines_list.append((response['Medicine'][i][0], response['Frequency'][j][0]))
                i+=1
                j+=1

        name = ''

        if 'Name' in response:
            name = response['Name'][0]


        return render_template("scan_result.html",name = name, medicine = medicines_list, output=response, pic = pic_name)
    else:
        return render_template("scan.html")
    
@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    if request.method=="GET":
        # token = {"token": app.config['token']}
        # print(token)
        # # access_headers = {"Authorization": "Bearer {}".format(app.config['token'])}
        # headers = {'Authorization': f"Bearer {token}"}
        # response = requests.get(
        #     api_url + '/dashboard', headers=headers
        #     ).json()
        
        url = "http://127.0.0.1:5000/dashboard"
        payload={}
        headers = {
        'Authorization': 'Bearer '+app.config['token']
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code==200:
            data = ast.literal_eval(response.text)
            # print(response.text)
            name = data['name']
            return render_template("dashboard.html", name = name)
        else:
            return "Invalid Token"
        
@app.route("/dashboard/upload", methods = ["GET", "POST"])
def dashboard_upload():
    if request.method=="GET":
        return render_template("scan_at_dashboard.html")
    else:
        image = request.files['prescription']

        pic_filename = secure_filename(image.filename)
        pic_name = str(uuid.uuid1()) + "_" + pic_filename

        image.save(os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_name))

        data = {}
        data['pic_name'] = pic_name
        data['email'] = app.config['email']

        url = "http://127.0.0.1:5000/dashboard/upload_prescription"
        headers = {
        'Authorization': 'Bearer '+app.config['token']
        }
        # r = requests.request(
        #     "POST",
        #     url,
        #     data=data,
        #     headers=headers
        # )
        response = requests.post(
            url,
            data,
            headers=headers
        )
        # response = requests.request("POST", url, headers=headers, data=data)
        return "hi"

if __name__=="__main__":
    app.run(debug=True, port=8000)