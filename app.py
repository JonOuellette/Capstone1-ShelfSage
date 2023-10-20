import os

from flask import Flask, render_template, redirect, request, session, jsonify, g, flash, url_for
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

@app.before_request
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

##############################################################################################################
#home page

# @app.route("/", methods=['GET', 'POST'])
# def home():
#     form = SearchForm()

# response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)
# data = response.json()
# total_search_per_query = data['totalItems']


@app.route('/', methods=['GET', 'POST'])
def home():
    form = SearchForm()
    search_query = ''
    search_type = ''

    # Extract pagination parameters or set default
    start_index = request.args.get('start', default=0, type=int)
    max_results = request.args.get('max', default=10, type=int)

    # Check if it's a form submission
    if form.validate_on_submit():
        search_query = form.search_query.data
        search_type = form.search_type.data
    else:
        # If not form submission, it could be page navigation, so retrieve the query from URL params
        search_query = request.args.get('query', '')
        search_type = request.args.get('type', '')

    if search_query:
        params = {
            'q': f'{search_type}:{search_query}',
            'startIndex': start_index,
            'maxResults': max_results
        }

        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)

        if response.status_code == 200:
            data = response.json()
            total_results = data.get('totalItems', 0)
            results = data.get('items', [])

            # Render the same page with results
            return render_template('home.html', form=form, results=results, total_results=total_results, start=start_index, max=max_results, query=search_query, type=search_type)
        else:
            flash(f'Error: Unable to fetch search results. Status code {response.status_code}', 'danger')

    return render_template('home.html', form=form)



