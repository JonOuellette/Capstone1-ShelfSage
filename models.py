from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(15), nullable=False, unique = True)
    email = db.Column(db.String(40), nullable=False, unique=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    bookshelves = db.relationship('BookShelf', backref='user', lazy=True)

    library = db.relationship('Book', secondary='user_library', backref='book_owners', lazy=True)


    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, first_name, last_name):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            first_name = first_name,
            last_name = last_name
        )

        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String, nullable=False)
    subtitle = db.Column(db.String)
    authors = db.Column(db.String, nullable=False)
    publisher = db.Column(db.String)
    published_date = db.Column(db.String)
    description = db.Column(db.Text)
    categories = db.Column(db.Text)
    image_links = db.Column(db.String)
    info_link = db.Column(db.String)
    volume_id = db.Column(db.String(50), unique=True)

    
class BookShelf(db.Model):
    __tablename__ = "bookshelves"
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

     # Define foreign key to link to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

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


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)