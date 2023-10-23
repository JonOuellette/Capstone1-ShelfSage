$(document).ready(function() {
    // Rename bookshelf
    $('.rename-bookshelf').click(function() {
        let bookshelfDiv = $(this).closest('.bookshelf');
        let bookshelfId = bookshelfDiv.data('bookshelf-id');
        let newName = prompt('Enter new bookshelf name:');

        if (newName) {
            axios.post('/rename_bookshelf/' + bookshelfId, { newName: newName })
                .then(function(response) {
                    if(response.data.success) {
                        bookshelfDiv.find('.bookshelf-name').text(newName);
                    } else {
                        console.error('Failed to rename:', response.data.error);
                    }
                })
                .catch(function(error) {
                    console.error('There was an error!', error);
                });
        }
    });

    // Delete bookshelf
    $('.delete-bookshelf').click(function() {
        let bookshelfDiv = $(this).closest('.bookshelf');
        let bookshelfId = bookshelfDiv.data('bookshelf-id');

        axios.post('/delete_bookshelf/' + bookshelfId)
            .then(function(response) {
                if (response.data.success) {
                    bookshelfDiv.remove();
                } else {
                    console.error('Failed to delete:', response.data.error);
                }
            })
            .catch(function(error) {
                console.error('Deletion request failed', error);
            });
    });

    // Reordering bookshelves
    $('.bookshelves-container').sortable({
        stop: function(event, ui) {
            let newOrder = $(this).sortable('toArray', { attribute: 'data-bookshelf-id' });

            axios.post('/reorder_bookshelves', { newOrder: newOrder })
                .then(function(response) {
                    console.log(response.data);
                })
                .catch(function(error) {
                    console.error('There was an error reordering the bookshelves!', error);
                });
        }
    });

    // Add book to bookshelf
    $('.bookshelf-selector').change(function() {
        let bookElement = $(this).closest('.media');
        let selectedBookshelfId = $(this).val();
        let volumeId = $(this).data('volume-id');

        if (selectedBookshelfId) {
            axios.post('/add_book_to_bookshelf/' + selectedBookshelfId + '/' + volumeId)
                .then(function(response) {
                    if (response.data.success) {
                        console.log('Book added successfully');
                        let bookshelfDiv = $('.bookshelf[data-bookshelf-id="' + selectedBookshelfId + '"]');
                        let bookList = bookshelfDiv.find('.list-group');
                        bookElement.detach().appendTo(bookList);
                    } else {
                        console.error('Failed to add book:', response.data.error);
                    }
                })
                .catch(function(error) {
                    console.error('There was an error adding the book!', error);
                });
        }
    });

    $('.delete-book').click(function() {
        var bookId = $(this).data('book-id');  // Getting the book ID from the button's data attribute
        var bookElement = $(this).closest('.media');  // Selecting the whole book element for later removal
    
        axios.post('/delete_book_from_library/' + bookId)
            .then(function(response) {
                if (response.data.success) {
                    // If the request was successful, remove the book element from the DOM
                    bookElement.remove();
                } else {
                    console.error('Failed to delete the book:', response.data.error);
                }
            })
            .catch(function(error) {
                console.error('Error occurred:', error);
            });
    });

    
});
// handling the removal of books from a bookshelf
$(document).on('click', '.remove-book', function(event) {
    event.preventDefault();  
    
    var bookElement = $(this).closest('li');  // Selecting the whole list item for the book.
    var bookId = $(this).data('book-id');  // Getting the book ID from the link's data attribute.

    // Traversing up the DOM to find the closest parent '.bookshelf' element and retrieve its data attribute.
    var bookshelfId = $(this).closest('.bookshelf').data('bookshelf-id'); 

    // Check if bookshelfId was successfully retrieved
    if(bookshelfId) {
        axios.post('/remove_book_from_bookshelf/' + bookshelfId + '/' + bookId)
            .then(function(response) {
                if (response.data.success) {
                    // If the request was successful, remove the book element from the DOM.
                    bookElement.remove();
                } else {
                    console.error('Failed to remove the book:', response.data.error);
                }
            })
            .catch(function(error) {
                console.error('Error occurred:', error);
            });
    } else {
        console.error('Failed to retrieve bookshelf ID.');
    }
});

