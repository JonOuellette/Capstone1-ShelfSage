import os

from flask import Flask, render_template, redirect, request, session, jsonify, g, flash
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import requests

from secretkeys import MY_SECRET_KEY
from models import connect_db, User, db, Book, BookShelf
from forms import SearchForm, RegisterForm, LoginForm

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/ShelfSage'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', MY_SECRET_KEY)
# toolbar = DebugToolbarExtension(app)

connect_db(app)

API_BASE_URL = "https://www.googleapis.com/books/v1/"


####################################################
# User signup/login/logout

@app.before_reqeust
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    
    else:
        g.user = None

def user_login(user):
    """Log in user"""

    session[CURR_USER_KEY] = user.id

def user_logout():
    """Logout user"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods = ['GET', 'POST'])
def signup(): 
    """Handles user signup. 
        Creates new users and adds them to the database.
    """

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    
    form = RegisterForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username = form.username.data,
                password = form.password.data,
                email = form.email.data,
                first_name = form.first_name.data,
                last_name = form.last_name.data
            )
            db.session.commit()
        
        except IntegrityError as e:
            flash("Username already taken", 'danger'),
            return render_template('signup.html', form = form)
        
        user_login(user)

        return redirect("/")
    
    else: 
        return render_template('signup.html', form=form)

@app.route('/login', methods= ["GET", "POST"])
def login():
    """Handles user login"""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            user_login(user)
            flash(f"Hello {user.username}!", "success")
            return redirect("/")
        
        flash("Invalid credentials", 'danger')
    
    return render_template('login.html' ,form=form)


@app.route('/logout', methods = ["GET", "POST"])
def logout():
    """Handles logging out user."""

    user_logout()

    flash("You have successfully logged out", 'success')

    return redirect("/login")



@app.route("/")
def homepage():


    return render_template("templates/index.html")