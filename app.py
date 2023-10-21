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
            print(data)
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

    # Debugging line to print all form data to console
    print(request.form)  
    print('FORM DATA:', request.form)    
    
    
     # Make a request to the Google Books API to get the specific volume details
    response = requests.get(f'https://www.googleapis.com/books/v1/volumes/{volume_id}')

    )
           

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


@app.route('/book_details/<string:volume_id>')
def book_details(volume_id):
    book = None
    # Check if the user is logged in and try to retrieve the book from their library.
    # if g.user:
    #     book = Book.query.filter_by(volume_id=volume_id).first()
        
    # If the user is not logged in or the book is not in their library,
    # fetch the book details from the Google Books API.
    if book is None:
        api_url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                book_data = response.json()
                book = book_data.get('volumeInfo', {})
            else:
                flash('Book not found.', 'danger')
                return redirect(url_for('home'))
        except requests.RequestException as e:
            flash('Error requesting book details.', 'danger')
            return redirect(url_for('home'))
    
    # Render the template with book details from either the database or the API.
    return render_template('book_details.html', book=book)