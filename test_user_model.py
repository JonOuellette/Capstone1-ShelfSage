import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Book, BookShelf, UserLibrary, BookshelfContent

os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/ShelfSage-test')
app.config['WTF_CSRF_ENABLED'] = False
from app import app

class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        # creating a user instance for testing
        self.username = "testuser"
        self.password = "hashed_password"
        self.email = "test@test.com"
        self.user = User.signup(username=self.username, 
                                email=self.email,
                                password=self.password, 
                                first_name="Test",
                                last_name="User")
        self.user_id = 1111
        self.user.id = self.user_id

        db.session.commit()

        self.user = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        # User should have no bookshelves & no books in the library initially
        self.assertEqual(len(self.user.bookshelves), 0)
        self.assertEqual(len(self.user.library), 0)

    ####
    #
    # Signup Tests
    #
    ####

    def test_valid_signup(self):
        test_user = User.signup("validuser", "valid@email.com", "password123", "Valid", "User")
        uid = 9999
        test_user.id = uid
        db.session.commit()

        user = User.query.get(uid)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "validuser")
        self.assertEqual(user.email, "valid@email.com")
        self.assertNotEqual(user.password, "password123")  # Password should be hashed
        self.assertTrue(user.password.startswith("$2b$"))  # bcrypt hash prefix

    def test_invalid_username_signup(self):
        invalid = User.signup(None, "test@test.com", "password", "Test", "User")
        uid = 123456789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid = User.signup("testuser2", None, "password", "Test", "User")
        uid = 123789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testuser3", "test3@test.com", None, "Test", "User")
        # You can add here checking context.exception messages if necessary

    ####
    #
    # Authentication Tests
    #
    ####

    def test_valid_authentication(self):
        u = User.authenticate(self.user.username, "hashed_password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.user_id)

    def test_invalid_username_auth(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user.username, "badpassword"))