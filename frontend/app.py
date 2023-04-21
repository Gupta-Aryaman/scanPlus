from flask import Flask, render_template, request, redirect
import requests

app = Flask(__name__)

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
        return ""
    else:
        status = request.args.get('status')
        return render_template("login.html", status=status)
    
if __name__=="__main__":
    app.run(debug=True, port=8000)