# Capstone1-ShelfSage

This application serves as a personal book management system, allowing users to leverage the Google Books API to search for books, create their own bookshelves, and add or remove books from these shelves. Built with Python and Flask, it offers a dynamic web interface for easy interaction.

Implemented features include:

1. **Book Search**: Powered by Google Books API, users can search for books by title, author, or ISBN, accessing a wide range of book collections.
   
2. **Personal Bookshelves**: Users can create their unique bookshelves, categorizing their reads for different genres, preferences, or reading status.

3. **Book Management**: Adding and removing books from their shelves allow users to organize their reading lists actively.

## User Flow

1. **Homepage**: Users are greeted with a simple interface that allows them to search books and obtain book details without logging in or creating a profile.

2. **User Login**  When users login they are taken to there personal library.  This allows users to add books to there library and create bookshelfs.

3. **Creating a Bookshelf**: By visiting the 'Create a New Bookshelf' section, users can form a new bookshelf by giving it a name and submitting the form.

4. **Organizing Bookshelf**: From the search results, users can easily add books to their chosen bookshelf or remove books they've already read or wish to take out from the list.

5. **Managing Bookshelves**: Users can view their shelves, see the books they contain, and continue to organize.


API: https://www.googleapis.com/books/v1/

- **Frontend**: HTML, CSS, JavaScript (with libraries such as jQuery)
- **Backend**: Python with Flask framework
- **API**: Google Books API
- **Deployment Platform**: [Render, ElephantSQL]