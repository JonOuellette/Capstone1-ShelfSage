from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(15), nullable=False, unique = True)
    email = db.Column(db.String(40), nullable=False, unique=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String, nullable=False)
    authors = db.Column(db.String, nullable=False)
    publisher = db.Column(db.String)
    publisher_date = db.Column(db.Date)

class BookShelf(db.Model):
    __tablename__ = "bookshelves"
    
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

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
