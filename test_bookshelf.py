import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Book, BookShelf, UserLibrary, BookshelfContent

os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/ShelfSage-test')

from app import app

class BookShelfModelTestCase(TestCase):
    """Test features related to the BookShelf model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        
        # Create a user instance for testing
        self.user = User.signup("testuser", "test@test.com", "password", "Test", "User")
        self.user_id = 1111
        self.user.id = self.user_id

        # Create bookshelf instances
        self.bookshelf1 = BookShelf(name="Shelf1", user_id=self.user_id)
        self.bookshelf2 = BookShelf(name="Shelf2", user_id=self.user_id)

        # Create book instances
        self.book1 = Book(title="1984", author="George Orwell")
        self.book2 = Book(title="Animal Farm", author="George Orwell")

        db.session.add_all([self.user, self.bookshelf1, self.bookshelf2, self.book1, self.book2])
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_create_bookshelves(self):
        self.assertEqual(BookShelf.query.count(), 2)

    def test_add_books_to_shelves(self):
        self.bookshelf1.books.append(self.book1)
        self.bookshelf2.books.append(self.book2)

        db.session.commit()

        self.assertEqual(len(self.bookshelf1.books), 1)
        self.assertEqual(len(self.bookshelf2.books), 1)

    def test_rename_bookshelf(self):
        self.bookshelf1.name = "Favorites"
        db.session.commit()

        renamed_shelf = BookShelf.query.filter_by(name="Favorites").first()
        self.assertIsNotNone(renamed_shelf)

    def test_rename_bookshelf_no_input(self):
        original_name = self.bookshelf1.name

        # Simulate renaming with empty input
        self.bookshelf1.name = ""  
        db.session.commit()

        # Refresh the object state after the attempted commit
        db.session.refresh(self.bookshelf1)

        # Check if the bookshelf's name is still the original, meaning the rename was unsuccessful
        self.assertEqual(self.bookshelf1.name, original_name)

    def test_move_book_between_shelves(self):
        self.bookshelf1.books.append(self.book1)
        db.session.commit()

        # Logic to remove a book from one shelf and add to another
        self.bookshelf1.books.remove(self.book1)
        self.bookshelf2.books.append(self.book1)
        db.session.commit()

        self.assertEqual(len(self.bookshelf1.books), 0)
        self.assertEqual(len(self.bookshelf2.books), 1)

    def test_remove_book_from_shelf(self):
        self.bookshelf1.books.append(self.book1)
        db.session.commit()

        self.bookshelf1.books.remove(self.book1)
        db.session.commit()

        self.assertEqual(len(self.bookshelf1.books), 0)

    def test_delete_book_from_shelf(self):
        self.bookshelf1.books.append(self.book1)
        db.session.commit()

        # Assuming 'delete_book' method is defined and removes the book from the database
        self.bookshelf1.delete_book(self.book1)

        self.assertEqual(len(self.bookshelf1.books), 0)

    def test_delete_bookshelf_with_books(self):
        self.bookshelf1.books.append(self.book1)
        db.session.commit()

        db.session.delete(self.bookshelf1)

        # If your logic prevents deletion of non-empty shelves, an exception should be raised
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()

    def test_create_bookshelf_without_name(self):
        invalid_shelf = BookShelf(name="", user_id=self.user_id)

        db.session.add(invalid_shelf)

        # Integrity error should be raised due to the empty name
        with self.assertRaises(exc.IntegrityError):
            db.session.commit()
