$(document).ready(function() {

    function refreshBookActions() {
        // For each book in a bookshelf, show the "Remove" button.
        $('.bookshelf .list-group-item').each(function() {
            $(this).find('.remove-book-btn').show();
            $(this).find('.delete-book').hide(); // If there's a delete button within a bookshelf, ensure it's hidden.
        });

        // For books not in a bookshelf, show the "Delete" button.
        $('.media:not(.bookshelf .media)').each(function() {
            $(this).find('.delete-book').show();
            $(this).find('.remove-book-btn').hide(); // In case there's a remove button here, ensure it's hidden.
        });
    }

    // Call this function when the page loads.
    refreshBookActions();

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

    // Listens for a change in the bookshelf selector.
    $('.bookshelf-selector').change(function() {
        let bookElement = $(this).closest('.media'); // This is the HTML element of the book.
        let selectedBookshelfId = $(this).val(); // This is the ID of the bookshelf you're adding the book to.
        let volumeId = $(this).data('volume-id'); // This is the volume ID of the book (retrieved from the data attribute).
        console.log(bookElement);  
        // Check if a bookshelf was selected.
        if (selectedBookshelfId) {
            // Send a request to the server to add the book to the bookshelf.
            axios.post('/add_book_to_bookshelf/' + selectedBookshelfId + '/' + volumeId)
                .then(function(response) {
                    console.log('Server response received:', response.data);
                    // This block is entered if the server responded successfully.
                    if (response.data.success) {
                        console.log('Book added successfully');

                        // Find the bookshelf in the DOM that the book was added to.
                        let bookshelfDiv = $('.bookshelf[data-bookshelf-id="' + selectedBookshelfId + '"]');
                        let bookList = bookshelfDiv.find('.list-group'  );

                        // Detach the book element from wherever it is and   append it to the bookshelf list.
                        bookElement.detach().appendTo(bookList);    

                        
                        // finds an existing 'Remove' button.
                        let removeBtn = bookElement.find('.remove-book-btn');
                        // If the 'Remove' button doesn't exist (which might be the case if the book was not in a bookshelf before),
                        if (removeBtn.length === 0) {
                        //checks if teh remove button was found.
                            removeBtn = $('<button class="remove-book-btn btn btn-danger">Remove</button>');
                            bookElement.append(removeBtn);
                            console.log(removeBtn)
                        }

                        // Show the 'Remove' button.
                        removeBtn.show();

                        // Set the 'data-volume-id' and 'data-bookshelf-id' attributes on the 'Remove' button. 
                        removeBtn.attr('data-volume-id', volumeId); // <-- Sets the volume ID for the book.
                        removeBtn.attr('data-bookshelf-id', selectedBookshelfId); // <-- Sets the bookshelf ID.

                        // Hide the 'Delete' button that's meant for when the book is not in any bookshelf.
                        bookElement.find('.delete-book').hide();

                        refreshBookActions(); 

                    } else {
                    // The server responded with an error message, so we log it to the console.
                    console.error('Failed to add book:', response.data.error);
                    }
                })
                .catch(function(error) {
                
                console.error('There was an error adding the book!', error);
                });
        }
    });


    $('.delete-book').click(function() {
        let bookId = $(this).data('book-id');  // Getting the book ID from the button's data attribute
        let bookElement = $(this).closest('.media');  // Selecting the whole book element for later removal
    
        axios.post('/delete_book_from_library/' + bookId)
            .then(function(response) {
                if (response.data.success) {
                    // If the request was successful, remove the book element from the DOM
                    console.log("Attempting to remove:", bookElement);
                    bookElement.remove();
                } else {
                    console.error('Failed to delete the book:', response.data.error);
                }
            })
            .catch(function(error) {
                console.error('Error occurred:', error);
            });
    });

      // Remove a book from a bookshelf
      $(document).on('click', '.remove-book-btn', function(event) {
        event.preventDefault();
    
        // Identifying the book element in the DOM.
        let bookElement = $(this).closest('.media');
    
        // Extracting the necessary data attributes.
        let volumeId = $(this).data('volume-id');
        let bookshelfId = $(this).data('bookshelf-id');
    
        if (volumeId) { 
            // Send a request to the server to remove the book from the bookshelf.
            axios.post('/remove_book_from_bookshelf/' + bookshelfId + '/' + volumeId)
                .then(function (response) {
                    if (response.data.success) {
                        console.log('Book removed successfully.');
    
                        // Detach the book element from its current location in the DOM.
                        bookElement.detach();
    
                        // Append the book element to the 'Other Books' section.
                        $('ul.list-unstyled').append(bookElement);
    
                        // Adjust visibility for action buttons.
                        bookElement.find('.remove-book-btn').hide(); // Hide the 'Remove from bookshelf' button.
                        bookElement.find('.add-to-bookshelf-btn').show(); // Show the 'Add to bookshelf' button, if you have one.
                        
                        // Here, you can also update other UI elements if necessary based on your application's needs.
    
                    } else {
                        console.error('Failed to remove book:', response.data.error);
                    }
                })
                .catch(function (error) {
                    console.error('An error occurred:', error);
                });
        } else {
            console.error('Volume ID is missing.');
        }
    });
    
  
    

});



