from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import User
from utils import read_file_text, generate_summary, generate_mcqs, text_to_pdf


app = Flask(__name__)

app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"


db.init_app(app)


os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing = User.query.filter_by(username=username).first()

        if existing:
            return "Username already exists"

        user = User(username=username, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        text_input = request.form.get("text_input")
        file = request.files.get("file_input")

        content = text_input or ""

        if file:

            filename = secure_filename(file.filename)

            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(path)

            content += read_file_text(path)


        summary = generate_summary(content)

        mcqs = generate_mcqs(content)

        pdf_path = os.path.join(app.config["OUTPUT_FOLDER"], "summary.pdf")

        text_to_pdf(summary, mcqs, pdf_path)

        return render_template("result.html", summary=summary, mcqs=mcqs)

    return render_template("dashboard.html")


@app.route("/download")
def download():

    path = os.path.join(app.config["OUTPUT_FOLDER"], "summary.pdf")

    return send_file(path, as_attachment=True)


@app.route("/logout")
def logout():

    session.pop("user_id", None)

    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)