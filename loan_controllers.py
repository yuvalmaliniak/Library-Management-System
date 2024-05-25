import datetime
import requests

genre_values = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']


class LoanOperations:
    loan_data = []  # Temporary data storage (list of dictionaries)

    def __init__(self):
        self.id = 1  # Books ID

    def create_loan(self, data):
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


    # Function to get all books
    def get_all_loans(self,query_dict=None):
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

    def get_loan_by_id(self,book_id):
        for book in self.books_data:
            if book['id'] == str(book_id):
                return book, 200
        return None, 404


    # Function to delete a book by ID
    def delete_loan(self, book_id):
        for i, book in enumerate(self.books_data):
            if book['id'] == str(book_id):
                del self.books_data[i]
                self.ratings.deleteratings(book['id'])
                return book_id, 200
        # No book found, return 404 error code
        return None, 404
    def get_from_books(self, method, params):
        # Define the base URL
        url = "http://books-services:8090/books"
        
        # Check if the method is GET
        if method.upper() == "GET":
            try:
                # Make the GET request with the provided parameters
                response = requests.get(url, params=params)
                
                # Raise an exception if the request was unsuccessful
                response.raise_for_status()
                
                # Return the JSON response
                return response.json()
            except requests.exceptions.RequestException as e:
                # Handle exceptions (e.g., network problems, invalid responses)
                print(f"An error occurred: {e}")
                return None
        else:
            print("Invalid method. Only 'GET' is supported.")
            return None
        