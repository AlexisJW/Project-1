import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def add_user(username, password):
        insert_user = User(username = username, password = password)
        db.session.add(insert_user)
        db.session.commit()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

class Books(db.Model):
    __tablename__ = "books"
    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.String, nullable=False)

def add_comment(username, comment, title, author, rating):
        insert_comment = Comments(username = username, comment = comment, title = title, author = author, rating = rating)
        db.session.add(insert_comment)
        db.session.commit()

class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    comment = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
