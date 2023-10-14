import os

from flask import Flask, render_template, redirect, request, session, jsonify, g, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import requests

from secretkeys import MY_SECRET_KEY

app = Flask(__name__)
app.app.context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/ShelfSage'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', MY_SECRET_KEY)
toolbar = DebugToolbarExtension(app)


API_BASE_URL = "https://www.googleapis.com/books/v1/"