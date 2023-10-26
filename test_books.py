import os
from unittest import TestCase
from sqlalchemy import exc
import requests_mock

from models import db, User, Book, BookShelf, UserLibrary, BookshelfContent

os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost/ShelfSage-test'

from app import app

class BookModelTestCase(TestCase):
    """Test features related to books."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        # creating a user instance for testing
        self.user = User.signup(username="testuser", 
                                email="test@test.com",
                                password="hashed_password", 
                                first_name="Test",
                                last_name="User")
        self.user_id = 8888  # just a random id for testing
        self.user.id = self.user_id

        self.book = Book(title="Test Book", volume_id="123456")  # add necessary fields
        db.session.add(self.book)

        
        db.session.commit()

        self.user = User.query.get(self.user_id)

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_search_books(self):
        # tests search books

        # Title search
        response = self.client.get('/search', query_string={'query': 'Lord of the Rings', 'type': 'title'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Lord of the Rings', response.data.decode())

        # Author search
        response = self.client.get('/search', query_string={'query': 'Alexandre Dumas', 'type': 'author'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Alexandre Dumas', response.data.decode())

        # Category search
        response = self.client.get('/search', query_string={'query': 'fantasy', 'type': 'category'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('fantasy', response.data.decode())

    def test_empty_search(self):
        # Test behavior when the search query is empty
        with self.client as c:
            response = c.post('/search', data={'search_query': '', 'search_type': 'title'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"No results found", response.data)

    def test_get_book_details(self):
        # Test the retrieval of book details, mocking external API requests if needed
        with requests_mock.Mocker() as mocker:
            api_response = {"volumeInfo": {"title": "Test Book", "authors": ["Author"]}}
            mocker.get('https://www.googleapis.com/books/v1/volumes/vxRIEAAAQBAJ', json=api_response)

            with self.client as c:
                response = c.get('/book_details/123456')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Test Book", response.data)

    def test_add_delete_book_in_library(self):
        # Assuming user authentication is handled, test adding/deleting a book

        with self.client:
            # simulate login
            self.client.post('/login', data=dict(username='testuser', password='hashed_password'))

            # Add book
            response = self.client.post('/add_book_to_library/vxRIEAAAQBAJ') 
            self.assertEqual(response.status_code, 302)  # or whatever status code you use for successful addition

            # Verify addition
            user = User.query.get(self.user_id)
            self.assertTrue(any(book.volume_id == 'vxRIEAAAQBAJ' for book in user.library))

            # Delete book
            response = self.client.post('/delete_book_from_library/vxRIEAAAQBAJ')  
            self.assertEqual(response.status_code, 200)  # or the status code you use for successful deletion

            # Verify deletion
            self.assertFalse(any(book.volume_id == 'vxRIEAAAQBAJ' for book in user.library))

    def test_unauthorized_book_addition(self):
        # Test that an unauthorized user cannot add a book
        response = self.client.post('/add_book_to_library/123')
        self.assertIn(response.status_code, [401, 302])  # or whatever status codes you use for unauthorized/redirects

    def test_add_existing_book_to_library(self):
        # Test behavior when trying to add a book that already exists in the user's library
        with self.client:
            self.client.post('/login', data=dict(username='testuser', password='hashed_password'))

            # Attempt to add again
            response = self.client.post('/add_book_to_library/vxRIEAAAQBAJ')

            # Check for a specific message or response scenario
            self.assertIn('already in your library', response.data.decode())

            # Verify no duplicates
            user = User.query.get(self.user_id)
            book_instances = [book for book in user.library if book.volume_id == 'vxRIEAAAQBAJ']
            self.assertEqual(len(book_instances), 1)  # there should only be one instance


