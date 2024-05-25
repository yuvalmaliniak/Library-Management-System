import datetime
import requests

genre_values = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']


class BookOperations:
    books_data = []  # Temporary data storage (list of dictionaries)

    def __init__(self):
        self.id = 1  # Books ID
        self.ratings = Ratings()

    def create_book(self, data):
        # Check validity: Missing fields, existing ID, existing ISBN
        if 'title' not in data or 'ISBN' not in data or 'genre' not in data:
            error_message = "Missing fields"
            return error_message, 422
        if None in (data['title'], data['ISBN'], data['genre']):
            error_message = "Missing fields"
            return error_message, 422
        for book in self.books_data:
            if book['ISBN'] == data['ISBN']:
                error_message = "There already exists a book in /book with this ISBN number"
                return error_message, 422
                
        # Extract required data from the POST request
        genre = data['genre']
        isbn = data['ISBN']
        if genre not in genre_values:
            error_message = "genre is not one of the accepted values"
            return error_message, 422
        # Enter data into the new book
        new_book = {
            'title': data['title'],
            'ISBN': data['ISBN'],
            'genre': data['genre'],
            'id': str(self.id)
        }
        self.id+=1
        # Handle Google API part
        google_books_data, error_code = self.googleapi(isbn)
        # Check if the call to Google went smooth
        if error_code == 200:
            new_book.update(google_books_data)
            length = len(new_book['authors'])
            # Make sure that multiple authors are being added by 'and' between their names.
            author = ""
            for i, value in enumerate(new_book['authors']):
                if i == (length-1):
                    author += value
                else:
                    author += value + " and "
            new_book['authors'] = author
        else:
            return google_books_data, error_code
        self.books_data.append(new_book)
        self.ratings.create_rating_data(self.id-1, new_book['title'])
        return new_book['id'], 201

    def googleapi(self,isbn):
        # Call Google Books API to get additional book information
        google_api_url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
        google_response = requests.get(google_api_url)
        google_params = {}
        missing = "missing"
        if google_response.status_code == 200:
            if google_response.json()['totalItems'] == 0:
                google_params = {
                    'authors': missing,
                    'publisher': missing,
                    'publishedDate': missing,
                }
                return google_params, 200
            # Extract the relevant data
            google_data = google_response.json()['items'][0]['volumeInfo']
            authors = google_data.get('authors')
            publisher = google_data.get('publisher')
            publishedDate = google_data.get('publishedDate')
            if publishedDate:
                try:
                    # Attempt to parse the published date string as a date object
                    parsed_date = datetime.datetime.strptime(publishedDate, '%Y-%m-%d')
                    # If the date is successfully parsed, format it as 'YYYY-MM-DD'
                    formatted_date = parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        # If parsing as 'YYYY-MM-DD' fails, try parsing as 'YYYY'
                        parsed_year = datetime.datetime.strptime(publishedDate, '%Y')
                        formatted_date = parsed_year.strftime('%Y')
                    except ValueError:
                        # If parsing as 'YYYY' also fails, set the value to 'missing'
                        formatted_date = missing
                publishedDate = formatted_date
            else:
                publishedDate = missing
            if authors is None:
                authors = missing
            if publisher is None:
                publisher = missing
            # Create the new book dictionary
            google_params = {
                'authors': authors,
                'publisher': publisher,
                'publishedDate': publishedDate,
            }
        else:
            error_message = "Unable to connect to Google API"
            return error_message, 500
        return google_params, 200



    # Function to get all books
    def get_all_books(self,query_dict=None):
        returned_books = []
        if query_dict:
            # Handle all query params. The check for validity is being done in main
            for book in self.books_data:
                if all(book.get(query) == value for query, value in query_dict.items()):
                    returned_books.append(book)
        else:
            returned_books = self.books_data
        return returned_books, 200

    # Function to get a single book by ID

    def get_book_by_id(self,book_id):
        for book in self.books_data:
            if book['id'] == str(book_id):
                return book, 200
        return None, 404

    # Function to update a book by ID
    def update_book(self, book_id, data):
        all_keys = data.keys()
        book_fields = ["title", "ISBN", "genre", "authors", "publisher", "publishedDate", "id"]
        for key in book_fields:
            # Check if all keys are in the PUT request. If not, return 422 error code
            if key not in all_keys:
                return "missing fields", 422
            if key == "genre":
                # Check the validity of genre
                if data[key] not in genre_values:
                    return "genre is not one of the accepted values", 422
        index = 0
        # Extract the book id if exists. If not, return 404 error code.
        for book in self.books_data:
            if book['id'] == str(book_id):
                break
            index += 1
        if index >= len(self.books_data):
            return "No such book with the given ID", 404
        for key in all_keys:
            # Update the book in the DB
            self.books_data[index][key] = data[key]
        return book_id, 200

    # Function to delete a book by ID
    def delete_book(self, book_id):
        for i, book in enumerate(self.books_data):
            if book['id'] == str(book_id):
                del self.books_data[i]
                self.ratings.deleteratings(book['id'])
                return book_id, 200
        # No book found, return 404 error code
        return None, 404
    def getRating(self):
        return self.ratings


class Ratings:
    def __init__(self):
        self.ratings_data = []

    def create_rating_data(self,id,title):
        values = []
        new_rating_entry = {
            'values': values,
            'average': 0,
            'title': title,
            'id': str(id)
        }
        self.ratings_data.append(new_rating_entry)

    def add_values_to_ratings(self,id,value):
        index = False
        avg=0
        for bookrating in self.ratings_data:
            # Find the id in the rating DB and add the value to the values array.
            if bookrating['id'] == str(id):
                bookrating['values'].append(value)
                count = 0
                index = True
                for value in bookrating['values']:
                    count += value
                avg = count/len(bookrating['values'])
                bookrating['average'] = avg
        if index:
            # We added value, so return the avg
            return avg, 200
        else:
            return "Book not found", 404

    def deleteratings(self, book_id):
        for i, rating in enumerate(self.ratings_data):
            if rating['id'] == book_id or str(rating['id']) == book_id:
                del self.ratings_data[i]
                return
    def get_rating_by_id(self,bookid):
        for rating in self.ratings_data:
            if rating['id'] == str(bookid):
                return rating, 200
        return {}, 200  # No Book with given id

    def get_all_ratings(self):
        return self.ratings_data, 200

    def top(self):
        # Extract all scores with more than 3 values
        book_averages = [rating['average'] for rating in self.ratings_data if len(rating['values']) >= 3]

        # Find the top 3 unique scores
        top_scores = sorted(set(book_averages), reverse=True)[:3]

        # Filter books that have top scores
        top_books = [
            {'id': rating['id'], 'title': rating['title'], 'average': rating['average']}
            for rating in self.ratings_data if rating['average'] in top_scores and len(rating['values']) >= 3
        ]

        # Sort books by average descending
        top_books_sorted = sorted(top_books, key=lambda x: x['average'], reverse=True)
        return top_books_sorted
