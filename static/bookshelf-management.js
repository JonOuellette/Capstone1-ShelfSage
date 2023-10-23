// bookshelf-management.js

$(document).ready(function() {
    $('.rename-bookshelf').click(function() {
        let bookshelfDiv = $(this).closest('.bookshelf');
        let bookshelfId = bookshelfDiv.data('bookshelf-id');
        let newName = prompt('Enter new bookshelf name:');
        if (newName) {
            $.ajax({
                url: '/rename_bookshelf/' + bookshelfId,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ newName: newName }),
                success: function(response) {
                    // Update the bookshelf's name in the UI or handle the response appropriately
                    bookshelfDiv.find('.bookshelf-name').val(newName);
                }
            });
        }
    });

    $('.delete-bookshelf').click(function() {
        if (confirm('Are you sure you want to delete this bookshelf?')) {
            let bookshelfDiv = $(this).closest('.bookshelf');
            let bookshelfId = bookshelfDiv.data('bookshelf-id');
            $.ajax({
                url: '/delete_bookshelf/' + bookshelfId,
                method: 'POST',
                success: function(response) {
                    // Remove the bookshelf from the UI or handle the response appropriately
                    bookshelfDiv.remove();
                }
            });
        }
    });

    // For reordering, the same concept applies
    $('.bookshelves-container').sortable({
        update: function(event, ui) {
            let newOrder = $(this).sortable('toArray', { attribute: 'data-bookshelf-id' });
            $.ajax({
                url: '/reorder_bookshelves',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ newOrder: newOrder }),
                success: function(response) {
                    // Handle the response. For instance, you might show a confirmation message
                }
            });
        }
    });
});
