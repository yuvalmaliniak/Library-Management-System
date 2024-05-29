import datetime
from flask import jsonify
import requests
import pymongo
import bson
from bson.objectid import ObjectId
genre_values = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']



class BookOperations:

    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://mongo:27017/")
        self.db = self.client['library']
        self.book_data = self.db['books']
        self.ratings_db = self.db['ratings']
        self.ratings = Ratings(self.ratings_db)


    def create_book(self, data):
        # Check validity: Missing fields, existing ID, existing ISBN
        if 'title' not in data or 'ISBN' not in data or 'genre' not in data:
            error_message = "Missing fields"
            return error_message, 422
        if None in (data['title'], data['ISBN'], data['genre']):
            error_message = "Missing fields"
            return error_message, 422
        existing_book = self.book_data.find_one({'ISBN': data['ISBN']})
        if existing_book:
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
            'genre': data['genre']
        }
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
        result = self.book_data.insert_one(new_book)
        bookID = str(result.inserted_id)
        if not bookID:
            return {"error": "Error in creating book"}, 422    
        self.ratings.create_rating_data(result.inserted_id, new_book['title'])
        return bookID, 201

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

    def convert_objectid(self, obj):
        for item in obj:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        print(obj)
        return obj
    

    # Function to get all books
    def get_all_books(self,query_dict=None):
        returned_books = []
        if query_dict:
            # Handle all query params. The check for validity is being done in main
            returned_books = list(self.book_data.find(query_dict))
        else:
            returned_books = list(self.book_data.find())
        print(returned_books)
        returned_books = self.convert_objectid(returned_books)
        return returned_books, 200

    # Function to get a single book by ID

    def get_book_by_id(self,book_id):
        try:
            book = self.book_data.find_one({'_id': ObjectId(book_id)})
            if book:
                book['_id'] = str(book['_id'])
                return book, 200
            else:
                return {"error": "No such book with the given ID"}, 404
        except:
            # Handle the case where the provided book_id is not a valid ObjectId
            return {"error": "Invalid ID"} , 404 

    # Function to update a book by ID
    def update_book(self, book_id, data):
        try:
            all_keys = data.keys()
            book_fields = ["title", "ISBN", "genre", "authors", "publisher", "publishedDate"]
            for key in book_fields:
                # Check if all keys are in the PUT request. If not, return 422 error code
                if key not in all_keys:
                    return "missing fields", 422
                if key == "genre":
                    # Check the validity of genre
                    if data[key] not in genre_values:
                        return "genre is not one of the accepted values", 422
            result = self.book_data.update_one({'_id': ObjectId(book_id)}, {'$set': data})
            if result.matched_count == 0:
                return "No such book with the given ID", 404
            return book_id, 200
        except:
            # Handle the case where the provided book_id is not a valid ObjectId
            return {"error": "Invalid ID"} , 404  

    # Function to delete a book by ID
    def delete_book(self, book_id):
        try:
            result = self.book_data.delete_one({'_id': ObjectId(book_id)})
            if result.deleted_count == 1:
                self.ratings.deleteratings(book_id)
                return book_id, 200
            return None, 404
        except:
            # Handle the case where the provided book_id is not a valid ObjectId
            return {"error": "Invalid ID"} , 404  
    def getRating(self):
        return self.ratings


class Ratings:
    def __init__(self, ratings_db):
        self.ratings_data = ratings_db

    def create_rating_data(self,id,title):
        values = []
        new_rating_entry = {
            'values': values,
            'average': 0,
            'title': title,
            '_id' : id
        }
        self.ratings_data.insert_one(new_rating_entry)

    def add_values_to_ratings(self, book_id, value):
        try:
            book_rating = self.ratings_data.find_one({'_id': ObjectId(book_id)})
            print(book_rating)
            if not book_rating:
                return "Book not found", 404

            self.ratings_data.update_one(
                {'_id': ObjectId(book_id)},
                {'$push': {'values': value}}
            )
            book_rating = self.ratings_data.find_one({'_id': ObjectId(book_id)})
            average = sum(book_rating['values']) / len(book_rating['values'])
            self.ratings_data.update_one(
                {'_id': ObjectId(book_id)},
                {'$set': {'average': average}}
            )
            return average, 200
        except:
            # Handle the case where the provided book_id is not a valid ObjectId
            return {"error": "Invalid ID"} , 404 


    def deleteratings(self, bookid):
        try:
            self.ratings_data.delete_one({'_id': ObjectId(bookid)})
        except:
            return {"error": "Invalid ID"} , 404 

    def get_rating_by_id(self,bookid):
        try:
            rating = self.ratings_data.find_one({'_id': ObjectId(bookid)})
            if rating:
                rating['_id'] = str(rating['_id'])
                return rating, 200
            return {}, 200
        except:
            return {"error": "Invalid ID"} , 404 

    def convert_objectid(self, obj):
        for item in obj:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        print(obj)
        return obj

    def get_all_ratings(self):
        ratings = list(self.ratings_data.find())
        ratings = self.convert_objectid(ratings)
        return ratings, 200

    def top(self):
        # Find all documents with at least 3 values
        eligible_books = list(self.ratings_data.find({'$expr': {'$gte': [{'$size': '$values'}, 3]}}))
        # If there are no eligible books, return an empty list
        if not eligible_books:
            return []

        # Extract all unique average scores
        unique_averages = sorted(set([book['average'] for book in eligible_books]), reverse=True)

        # Get the top 3 unique average scores
        top_averages = unique_averages[:3]

        # Find all books that have an average score in the top 3 averages
        top_books = [
            {'_id': str(rating['_id']), 'title': rating['title'], 'average': rating['average']}
            for rating in eligible_books if rating['average'] in top_averages
        ]

        # Sort top books by average score in descending order
        top_books_sorted = sorted(top_books, key=lambda x: x['average'], reverse=True)

        return top_books_sorted
