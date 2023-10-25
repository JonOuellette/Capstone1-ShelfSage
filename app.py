import os

from flask import Flask, render_template, redirect, request, session, jsonify, g, flash, url_for
# from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

import requests
import re
import random


app = Flask(__name__)
app.app_context().push()

from secretkeys import MY_SECRET_KEY
from models import connect_db, User, db, Book, BookShelf, BookshelfContent
from forms import SearchForm, RegisterForm, LoginForm, BookshelfForm

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
#home page and helper functions

@app.route('/')
def home():
    form = SearchForm()
    

    num_books = 5

    response = requests.get('https://www.googleapis.com/books/v1/volumes', params={'q': '*', 'maxResults': 40}) 

    random_books = []

    if response.status_code == 200:
        data = response.json()
        all_books = data.get('items', [])
        
        if all_books:
            random_books = random.sample(all_books, min(num_books, len(all_books)))

    return render_template('home.html', form=form, random_books = random_books)


def get_books(volume_id):
    #checks to see if the book is already in the database
    book = Book.query.filter_by(volume_id=volume_id).first()

    if book is None:
        #if the book does not exist in the database we then get the book data from the API
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes/{volume_id}")

        if response.status_code == 200:
            data = response.json()
            volume_info=data['volumeInfo']

            # Prepare the authors and categories for storage
            authors = volume_info.get('authors')
            # Convert authors list to string
            authors_str = ', '.join(authors) if authors else None  

            categories = volume_info.get('categories')
            # Convert categories list to string
            categories_str = ', '.join(categories) if categories else None  

            book = Book(
                title = volume_info.get('title'),
                subtitle = volume_info.get('subtitle'),
                authors = authors_str,
                publisher = volume_info.get('publisher'),
                published_date = volume_info.get('publishedDate'),
                categories = categories_str,
                description = volume_info.get('description'),
                image_links = volume_info.get('imageLinks', {}).get('thumbnail'),
                info_link = volume_info.get('infoLink'),
                volume_id=volume_id
                )

            db.session.add(book)
            db.session.commit()
        else:
            error_message = f"An error occurred while communicating with the Google Books API. Status code: {response.status_code}."
            return None, error_message
        
    return book


def get_book_from_db(volume_id):
    """Attempt to retrieve a book from the database using its volume_id."""
    book = Book.query.filter_by(volume_id=volume_id).first()
    
    return book
###############################################################################################################
###Search books, get book details and store in user library

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


@app.route('/book_details/<string:volume_id>')
def book_details(volume_id):
    book = None
    
    if book is None:
        api_url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                book_data = response.json()
                book = book_data.get('volumeInfo', {})
                book['volume_id'] = volume_id 
                
                #Debugging step: print the description to the console
                print(book.get('description'))

                description = book.get('description', '')
                #some books appeared to have a random " at the end of the description.  This was coming directly from the API.  Using regular expression to remove the random ".
                pattern = r'^"|"$'

                # re.sub() replaces the pattern with an empty string in 'description'.
                cleaned_description = re.sub(pattern, '', description)

                # Update the book information with the cleaned description.
                book['description'] = cleaned_description

            else:
                flash('Book not found.', 'danger')
                return redirect(url_for('home'))
        except requests.RequestException as e:
            flash('Error requesting book details.', 'danger')
            return redirect(url_for('home'))
    
    # Render the template with book details from either the database or the API.
    return render_template('book_details.html', book=book)

@app.route('/add_book_to_library/<string:volume_id>', methods=['POST'])
def add_book_to_library(volume_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Debugging line to print all form data to console
    print(request.form)  
    print('FORM DATA:', request.form)    

    book = get_books(volume_id)
    print(book)

    if book not in g.user.library:
        g.user.library.append(book)
        db.session.commit()
        flash("Book added to your library", "success")

    else: 
        flash("This book is already in your library.", "danger")

    return redirect(url_for('view_library'))    
               

@app.route('/my_library')
def view_library():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    # Retrieve books from the user's library and bookshelves
    books = g.user.library
    print(books)
    bookshelves = BookShelf.query.filter_by(user_id=g.user.id).all()
    
    # Prepare a list of all books that are in bookshelves
    shelved_books = [book for shelf in bookshelves for book in shelf.books]

    return render_template('user_library.html', books=books, bookshelves=bookshelves, shelved_books=shelved_books)


@app.route('/delete_book_from_library/<int:book_id>', methods=['POST'])
def delete_book_from_library(book_id):
    response_data = {'success': False}

    if not g.user:
        response_data['error'] = "Access unauthorized."
        return jsonify(response_data), 401

    # Use joinedload to load the book and its relationships to avoid multiple DB queries.
    book = Book.query.options(joinedload(Book.bookshelf_contents)).get_or_404(book_id)

    if book in g.user.library:
        # Remove the book from the user's library
        g.user.library.remove(book)

        # Remove book entries from all bookshelves it's part of
        for content in book.bookshelf_contents:
            db.session.delete(content)  # Deleting the BookshelfContent entries

        # Commit the changes to the database.
        db.session.commit()

        response_data['success'] = True
        response_data['message'] = "Book removed from your library."
    else:
        response_data['error'] = "This book is not in your library."

    return jsonify(response_data)



#####################################################################################################################################################
# Create and delete bookshelfs. Move books to bookshelfs.

@app.route('/create_bookshelf', methods=['GET', 'POST'])
def create_bookshelf():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = BookshelfForm()

    if form.validate_on_submit():
        new_bookshelf = BookShelf(
            name=form.name.data,
            description=form.description.data,
            user_id=g.user.id  
        )
        db.session.add(new_bookshelf)
        db.session.commit()
        flash("Bookshelf created!", "success")
        # Redirect to the new bookshelf's detail view
        return redirect("/my_library")  

    return render_template('create_bookshelf.html', form=form)


@app.route('/add_book_to_bookshelf/<int:bookshelf_id>/<string:volume_id>', methods=['POST'])
def add_book_to_bookshelf(bookshelf_id, volume_id):
    response_data = {'success': False}  

    if not g.user:
        response_data['error'] = "Access unauthorized."
        return jsonify(response_data), 401  

    bookshelf = BookShelf.query.get_or_404(bookshelf_id)

    if bookshelf.user_id != g.user.id:
        response_data['error'] = "Access unauthorized."
        return jsonify(response_data), 403  

    # Get the book from the database
    book = get_book_from_db(volume_id)

    if book is None:
        response_data['error'] = "No such book exists in the database."
        return jsonify(response_data), 404  

    # Check if the book is already in this bookshelf
    existing_content = BookshelfContent.query.filter_by(bookshelf_id=bookshelf.id, book_id=book.id).first()
    if existing_content:
        response_data['error'] = f"This book is already in {bookshelf.name}."
        return jsonify(response_data), 409  
    else:
        # Create a new BookshelfContent item and associate it with the book and bookshelf
        new_content = BookshelfContent(bookshelf_id=bookshelf.id, book_id=book.id)
        BookshelfContent.query.filter_by(book_id = book.id).delete()
        db.session.add(new_content)
        db.session.commit()

        response_data['success'] = True
        response_data['message'] = f"Book added to {bookshelf.name}"
        return jsonify(response_data)  

@app.route('/bookshelf/<int:bookshelf_id>')
def view_bookshelf(bookshelf_id):
    bookshelf = BookShelf.query.get_or_404(bookshelf_id)

    if bookshelf.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Get the books in this bookshelf through the BookshelfContent relationships
    books = [content.book for content in bookshelf.bookshelf_contents]  

    return render_template('user_library.html', bookshelf=bookshelf, books=books)

@app.route('/rename_bookshelf/<int:bookshelf_id>', methods=['POST'])
def rename_bookshelf(bookshelf_id):
    new_name = request.json.get('newName')
    bookshelf = BookShelf.query.get(bookshelf_id)  

    if bookshelf is None:
        return jsonify({'success': False, 'error': 'Bookshelf not found'}), 404

    # Update the name
    bookshelf.name = new_name  
    db.session.commit()  

    # Return success if the operation was successful
    return jsonify({'success': True})

@app.route('/delete_bookshelf/<int:bookshelf_id>', methods=['POST'])
def delete_bookshelf(bookshelf_id):
   # Authentication checks, data validation, and deletion logic here...
    # Locate the bookshelf and delete it
    bookshelf = BookShelf.query.get_or_404(bookshelf_id)

    if bookshelf.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    try:
        db.session.delete(bookshelf)
        db.session.commit()
    except Exception as e:
        # Log the exception here
        return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': True})

@app.route('/reorder_bookshelves', methods=['POST'])
def reorder_bookshelves():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Extract the new order from the request body
    new_order = request.json.get('newOrder')

    try:
        #  Assumes that the bookshelf has an order field which dictates the order in the user library 
      
        for index, bookshelf_id in enumerate(new_order):
            bookshelf = BookShelf.query.get(bookshelf_id)
            if bookshelf and bookshelf.user_id == g.user.id:  # Check ownership
                bookshelf.order = index  # Set the new order
                db.session.commit()
        return jsonify({'success': True, 'message': 'Bookshelves reordered successfully.'})
    except Exception as e:
        # Handle exceptions here
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/remove_book_from_bookshelf/<int:bookshelf_id>/<string:volume_id>', methods=['POST'])
def remove_book_from_bookshelf(bookshelf_id, volume_id):
    # Verifies that the user is logged in and has the right to modify this bookshelf
    if not g.user:
        return jsonify({"success": False, "error": "Access unauthorized"}), 401

    # Checks that both the bookshelf and book exist
    bookshelf = BookShelf.query.get_or_404(bookshelf_id)
    book = Book.query.filter_by(volume_id=volume_id).first()
    
    # Ensures both bookshelf and book are valid and found
    if bookshelf is None or book is None:
        
        return jsonify({"success": False, "error": "Bookshelf or Book not found"}), 404

    try:
        # Finds all the associatiosn of this book with any bookshelf
        associations = BookshelfContent.query.filter_by(book_id=book.id).all()  

        if len(associations) > 1:
            # The book is in multiple bookshelves, remove it only from the current one
            current_association = next((assoc for assoc in associations if assoc.bookshelf_id == bookshelf_id), None)
            if current_association:
                db.session.delete(current_association)
        else:
            # The book is only in the current bookshelf, we can remove the single association
            if associations:
                db.session.delete(associations[0])

        # Remove the association and save the change
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()  
        return jsonify({"success": False, "error": "Internal server error"}), 500
