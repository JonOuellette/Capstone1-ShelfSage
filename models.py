from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(15), nullable=False, unique = True)
    email = db.Column(db.String(40), nullable=False, unique=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    bookshelves = db.relationship('Bookshelf', backref='user', lazy=True)

    library = db.relationship('Book', secondary='user_library', backref='users', lazy=True)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String, nullable=False)
    subtitle = db.Column(db.String)
    authors = db.Column(db.String, nullable=False)
    publisher = db.Column(db.String)
    publisher_date = db.Column(db.Date)
    categories = db.Column(db.Text)
    image_links = db.Column(db.String)
    info_link = db.Column(db.String)
    volume_id = db.Column(db.String(50), unique=True)

    # Define a relationship with users (library)
    users = db.relationship('User', secondary='user_library', backref='library', lazy=True)

class BookShelf(db.Model):
    __tablename__ = "bookshelves"
    
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

     # Define foreign key to link to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Define a relationship with books (shelf content)
    books = db.relationship('Book', secondary='bookshelf_content', backref='bookshelves', lazy=True)

class UserLibrary(db.Model):
    __tablename__ = "user_library"

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))

class BookshelfContent(db.Model):
    __tablename__ = "bookshelf_content"

    id = db.Column(db.Integer, primary_key = True)
    bookshelf_id = db.Column(db.Integer, db.ForeignKey('bookshelves.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
