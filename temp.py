@app.route('/add_book_to_library', methods=['POST'])
def add_book_to_library():
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Debugging line to print all form data to console
    print(request.form)  
    print('FORM DATA:', request.form)    
    
    
     # Make a request to the Google Books API to get the specific volume details
    response = requests.get(f'https://www.googleapis.com/books/v1/volumes/{volume_id}')

    if response.status_code == 200:
        book_data = response.json()

        if book_data:    
            # Extract data from the form submission or API response
            volume_info = book_data.get('volumeInfo', {})
            title = volume_info.get('title')
            subtitle = volume_info.get('subtitle')
            authors = ', '.join(volume_info.get('authors', []))
            publisher = volume_info.get('publisher')
            published_date = volume_info.get('publishedDate')
            categories = ', '.join(volume_info.get('categories', []))
            image_links = volume_info.get('imageLinks', {}).get('thumbnail')
            info_link = volume_info.get('infoLink')
            book_id = request.form.get('book_id')

            # Check if the book already exists in the database
            existing_book = Book.query.filter_by(volume_id=volume_id).first()
            if existing_book is None:
                # Create a new book instance and add it to the database
                new_book = Book(
                    title=title,
                    subtitle=subtitle,
                    authors=authors,
                    publisher=publisher,
                    published_date=published_date,
                    categories=categories,
                    image_link=image_links,
                    info_link=info_link,
                    volume_id=volume_id,
                    book_id=book_id  
                )
                db.session.add(new_book)
                db.session.commit()

                # Add the book to the user's library
                g.user.library.append(new_book)  # Assuming 'library' is a relationship field
                db.session.commit()

                flash('Book added to your library!', 'success')
            else:
                # If the book is already in the user's library, notify the user
                if existing_book in g.user.library:
                    flash('You already have this book in your library.', 'info')
                else:
                    # Otherwise, add the book to the user's library
                    g.user.library.append(existing_book)
                    db.session.commit()
                    flash('Book added to your library!', 'success')

        else:
            flash('Book not found.', 'danger')
    else:
        flash('Failed to retrieve data from Google Books.', 'danger')

    return redirect(url_for('view_library'))