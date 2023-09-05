import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import json


if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    books = mongo.db.books.find()
    return render_template("books.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for('profile', username=session["user"]))
    return render_template("register.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    'profile', username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("signin.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for('signin'))


@app.route("/signout")
def signout():
    # remove user from session cookie
    flash("You have been signed out")
    session.pop("user")
    return redirect(url_for('signin'))


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book = {
            "category_name": request.form.get("category_name"),
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "book_description": request.form.get("book_description"),
            "created_by": session['user'],
            "reviews": request.form.get("reviews")
        
        }

        mongo.db.books.insert_one(book)
        flash("Book successfully added")
        return redirect(url_for("home"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_book.html",  categories=categories)


@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    book = mongo.db.books.find_one({'_id': ObjectId(book_id)})

    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "book_description": request.form.get("book_description"),
            "created_by": session['user'],
            "reviews": request.form.get("reviews")
        
        }

        mongo.db.books.update_one({"_id": ObjectId(book_id)}, {"$set": submit})
        flash("Book successfully updated")

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_book.html", book=book, categories=categories)


@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    flash("Book successfully deleted")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
