import os
import requests
import psycopg2

from flask import Flask, session, render_template, request, logging, url_for, redirect, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt
from sqlalchemy import or_, and_
from models import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()
        db = scoped_session(sessionmaker(bind=engine))
Session(app)

@app.route('/')
def index():
    books = Books.query.limit(20).all()
    ratings = []
    for book in books:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ALwzDvkMP8PEOuiOtTUD9g", "isbns": book.isbn})
        if res.status_code != 200:
                raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        book_json = data['books']
        rating = book_json[0]['average_rating']
        ratings.append(rating)

    return render_template('index.html', books = books, username_data = request.args.get('username_data'), ratings = ratings)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        username_data = User.query.filter((User.username == username and User.password == password)).first()

        if username_data is None:
            flash("Incorrect username!", "danger")
            return render_template("login.html")
        else:
                 if sha256_crypt.verify(password, username_data.password):
                     session["log"] = True
                     flash("You are login", "success")
                     return redirect(url_for('index', username_data = username))
                 else:
                     flash("Incorrect password!", "danger")
                     return render_template("login.html")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("repeat-pass")
        secure_password = sha256_crypt.encrypt(str(password))

        if password == confirm:
            # Add user.
            add_user(username, secure_password)
            flash("You are registered and now you can login!", "success")
            return redirect(url_for('login'))
        else:
            flash("password doesn't match", "danger")
            return render_template("signup.html")

    return render_template("signup.html")

@app.route('/logout')
def logout():
    session["log"] = False
    session.clear()
    return redirect(url_for('index'))

@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search = request.form.get("search")
        books = Books.query.filter(or_(Books.author.like(search), Books.title.like(search), Books.isbn.like(search)) ).all()
        username_data = request.args.get('username_data')
        ratings = []
        for book in books:
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ALwzDvkMP8PEOuiOtTUD9g", "isbns": book.isbn})
            if res.status_code != 200:
                    raise Exception("ERROR: API request unsuccessful.")
            data = res.json()
            book_json = data['books']
            rating = book_json[0]['average_rating']
            ratings.append(rating)

        if search is "":
            flash("Please enter an AUTHOR name, TITLE or ISBN !", "danger")
            return render_template('search.html', books = books, username_data = request.args.get('username_data'))
        if not books:
            flash("No such Book!", "danger")
            return render_template('search.html', books = books, username_data = request.args.get('username_data'))
        if username_data is None:
            flash("First off, You need to log before making a search!!!", "danger")
            return redirect(url_for('index'))

    return render_template('search.html', books = books, username_data = request.args.get('username_data'), ratings = ratings)


@app.route('/view', methods = ["GET", "POST"])
def view():
    username_data = request.args.get('username_data')
    title = request.args.get('title')
    author = request.args.get('author')
    comments = Comments.query.filter(and_(Comments.title.like(title), Comments.author.like(author)) ).all()

    if request.method == "POST":
        comments_username = Comments.query.filter(and_(Comments.title.like(title), Comments.author.like(author), Comments.username.like(username_data)) ).all()
        if not comments_username:
            comment = request.form.get("addComment")
            rating = request.form.get("rating")
            if rating is None:
                rating = 0
            else:
                rating = int(rating)

            add_comment(username_data, comment, title, author, rating)
            flash("commit!", "success")
            comments = Comments.query.filter(and_(Comments.title.like(title), Comments.author.like(author)) ).all()
        else:
            flash("You shouldn't be able to submit multiple reviews for the same book!", "danger")
            comments = Comments.query.filter(and_(Comments.title.like(title), Comments.author.like(author)) ).all()

        return render_template('view.html', username_data = request.args.get('username_data'), author = request.args.get('author'), title = request.args.get('title'), isbn = request.args.get('isbn'), year = request.args.get('year'), comments = comments, rating = request.args.get('rating'))

    return render_template('view.html', username_data = request.args.get('username_data'), author = request.args.get('author'), title = request.args.get('title'), isbn = request.args.get('isbn'), year = request.args.get('year'), comments = comments, rating = request.args.get('rating'))


@app.route("/api/<string:isbn>")
def book_api(isbn):
    api = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ALwzDvkMP8PEOuiOtTUD9g", "isbns": isbn})

    if api.status_code != 200:
            return jsonify({"error": "Invalid ISBN"}), 422

    book = Books.query.filter(Books.isbn.like(isbn)).all()
    data = api.json()
    bookJson = data['books']
    rating = bookJson[0]['average_rating']

    return jsonify({
    "title": book[0].title,
    "author": book[0].author,
    "year": book[0].year,
    "isbn": isbn,
    "review_count": bookJson[0]['reviews_count'],
    "average_score": bookJson[0]['average_rating']
})
