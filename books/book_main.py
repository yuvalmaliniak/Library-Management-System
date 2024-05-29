from flask import Flask,jsonify,request
from flask_restful import Resource, Api, reqparse
from book_controllers import BookOperations
import json
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)
connection_string = "mongodb://mongo:27017/"
client = MongoClient(connection_string)
db = client['library_database']
books_collection = db['books']
ratings_collection = db['ratings']
controller = BookOperations()



class Books(Resource):
    def post(self):
        # Check if the request is json. If not, return error 415 with relevant error message
        if not request.is_json or request.headers['Content-Type'] != 'application/json':
            return {"error": "Unsupported media type"}, 415
        args = request.get_json()
        try:
            # Handle the POST request
            desired_keys = ["title", "ISBN", "genre"]
            for key in desired_keys:
                if key not in args:
                    return {"error": "Missing required parameter"}, 422
            title = args["title"]
            isbn = args["ISBN"]
            genre = args["genre"]
            post_data = {
                "title": title,
                "ISBN": isbn,
                "genre": genre
            }
            output, error_code = controller.create_book(post_data)
            if error_code == 201:
                return {"id": output}, error_code
            else:
                return {"error": output}, error_code
        except json.JSONDecodeError as e:
            return {'error': 'Invalid JSON format'}, 415  # Return JSON with error message and HTTP status code 415 (Bad Request)

    def get(self):
        genre_values = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']
        query_params = request.args
        query_dictionary = query_params.to_dict()
        if query_params:
            if 'genre' in query_dictionary:
                if query_dictionary['genre'] not in genre_values:
                    return {"error": "genre is not one of the accepted values"}, 422
            return controller.get_all_books(query_dict=query_dictionary)
        else:
            # Handle the case where there are no query parameters
            # Call a method in the controller to get all books
            books, error_code = controller.get_all_books(query_dict=None)
            return books, error_code


class BookID(Resource):
    def get(self,bookid):
        books, error_code = controller.get_book_by_id(bookid)
        if books is not None:
            return books, error_code
        else:
            return {'error': 'Book not found'}, 404

    def put(self,bookid):
        # Logic to update a specific book using the book_id
        # Check if the request is json. If not, return error 415 with relevant error message
        if not request.is_json or request.headers['Content-Type'] != 'application/json':
            return {"error": "Unsupported media type"}, 415
        data = request.get_json()
        output, error_code = controller.update_book(bookid, data)
        if error_code == 200:
            return {"id": output}, 200
        else:
            return {'error': output},  error_code

    def delete(self,bookid):
        idofbook, error_code = controller.delete_book(bookid)
        if error_code == 200:
            return {"id": idofbook}, 200
        else:
            return {"error": "Book not found"}, error_code


class Ratings(Resource):
    def get(self):
        # Logic to fetch all ratings
        # Call the relevant function: one for GET with query, and one for GET without query.
        # If the query is not "id", return error code 422
        query_params = request.args
        if query_params == {}:
            return controller.ratings.get_all_ratings()
        elif "id" in query_params.keys():
            return controller.ratings.get_rating_by_id(query_params["id"])
        else:
            return {"error": "Unprocessable Content"}, 422


class SingleRating(Resource):
    def get(self,bookid):
        try:
            output, error_code = controller.ratings.get_rating_by_id(bookid)
            return output, error_code
        except json.JSONDecodeError as e:
            return {'error': 'Invalid JSON format'}, 415  # Return JSON with error message and HTTP status code 415 (Bad Request)

class RatingValues(Resource):
    def post(self, bookid):
        args = request.get_json()
        try:
            value = args["value"]
            output, error_code = controller.ratings.add_values_to_ratings(bookid, value)
            if error_code == 200:
                return {"avg": output}, error_code
            else:
                return {"error": output}, error_code
        except json.JSONDecodeError as e:
            return {'error': 'Invalid JSON format'}, 415  # Return JSON with error message and HTTP status code 415 (Bad Request)


class Top(Resource):
    def get(self):
        # Logic to fetch top-rated books or ratings
        try:
            top_sorted_books = controller.ratings.top()
            return top_sorted_books, 200
        except json.JSONDecodeError as e:
            return {'error': 'Invalid JSON format'}, 415  # Return JSON with error message and HTTP status code 415 (Bad Request)

api.add_resource(Books, '/books')
api.add_resource(BookID, '/books/<string:bookid>')
api.add_resource(Ratings, '/ratings')
api.add_resource(SingleRating, '/ratings/<string:bookid>')
api.add_resource(RatingValues, '/ratings/<string:bookid>/values')
api.add_resource(Top, '/top')

if __name__ == '__main__':
    # Define the API routes using Flask
    app.run(host='0.0.0.0', port=8000, debug=True)





