import os

from flask import Flask, render_template, redirect, request, session, jsonify, g, flash, url_for
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import requests

app = Flask(__name__)
app.app_context().push()

from secretkeys import MY_SECRET_KEY
from models import connect_db, User, db, Book, BookShelf
from forms import SearchForm, RegisterForm, LoginForm

CURR_USER_KEY = "curr_user"



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

@app.route('/')
def homepage():
    form = SearchForm()
    return render_template('home.html', form=form)

###############################################################################################################

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm(request.form)
    search_query = ''
    search_type = ''

    # Extract pagination parameters or set default
    start_index = request.args.get('start', default=0, type=int)
    max_results = request.args.get('max', default=10, type=int)

    
    if form.validate_on_submit():
        #Direct form submission
        search_query = form.search_query.data
        search_type = form.search_type.data
        return redirect(url_for('search', query=search_query, type=search_type, start=start_index, max=max_results))
    else:
        # If not form submission, it could be page navigation, so retrieve the query from URL params
        search_query = request.args.get('query', '')
        search_type = request.args.get('type', '')

    if search_query:
        #prepares the request parameters
        params = {
            'q': f'{search_type}:{search_query}',
            'startIndex': start_index,
            'maxResults': max_results
        }

        #Makes the API request
        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)

        if response.status_code == 200:
            data = response.json()
            total_results = data.get('totalItems', 0)
            results = data.get('items', [])

            # Render the same page with results
            return render_template('search_results.html', form=form, results=results, total_results=total_results, start=start_index, max=max_results, query=search_query, type=search_type)
        else:
            flash(f'Error: Unable to fetch search results. Status code {response.status_code}', 'danger')

    return render_template('search_results.html', form=form)


@app.route('/add_book_to_library', methods=['POST'])
def add_book_to_library():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Extract data from the form submission or API response
    print(request.form)  # Debugging line to print all form data to console
    print('FORM DATA:', request.form)
    book_id = request.form.get('book_id')  
    title = request.form.get('title')
    authors = request.form.get('authors')
    publisher = request.form.get('publisher')
    publisher_date = request.form.get("publisher_date")
    image_links = request.form.get('image_links')

    # other book details you want to include, extracted similarly

    print(f"book_id: {book_id}, title: {title}, authors: {authors}, publisher: {publisher}, publisher_date: {publisher_date}, image_links:{image_links}")
          
    # Check if the book already exists in the database
    book = Book.query.filter_by(volume_id=book_id).first()

    if book is None:
        # Create a new book instance and add it to the database
        book = Book(
            title=title,
            authors=authors, 
            publisher=publisher,
            publisher_date=publisher_date,
            image_links = image_links,
            volume_id=book_id,
            # ... set other fields ...
        )
        db.session.add(book)
        

    # Check if the book is already in the user's library
    if book not in g.user.library:
        # Add the book to the user's library and commit changes
        g.user.library.append(book)
        db.session.commit()
        flash('Book added to your library!', 'success')
    else:
        flash('You already have this book in your library.', 'info')

    return redirect(url_for('view_library'))   # or to a relevant location

@app.route('/my_library')
def view_library():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    # Retrieve books from the user's library
    books = g.user.library
    print(books) 
    return render_template('user_library.html', books=books)


@app.route('/delete_book_from_library/<book_id>', methods=['POST'])
def delete_book_from_library(book_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))  # or wherever your login route is

    # Get the book object
    book = Book.query.get_or_404(book_id)

    # Check if the book is actually in the user's library before attempting deletion
    if book in g.user.library:
        # Remove the book and update the database
        g.user.library.remove(book)
        db.session.commit()
        flash('Book removed from your library.', 'success')
    else:
        flash('This book is not in your library.', 'danger')

    return redirect(url_for('view_library'))


