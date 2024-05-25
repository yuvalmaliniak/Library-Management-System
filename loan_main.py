from flask import Flask,jsonify,request
from flask_restful import Resource, Api, reqparse
from loan_controllers import LoanOperations
import json
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)
client = MongoClient('mongodb://localhost:27017/')
loans = client['loans']
books = client['books']
controller = LoanOperations(loans,books)

class Loans(Resource):
    def post(self):
        # Check if the request is json. If not, return error 415 with relevant error message
        if not request.is_json or request.headers['Content-Type'] != 'application/json':
            return {"error": "Unsupported media type"}, 415
        args = request.get_json()
        try:
            # Handle the POST request
            desired_keys = ["memberName", "ISBN", "loanDate"]
            for key in desired_keys:
                if key not in args:
                    return {"error": "Missing required parameter"}, 422
            memberName = args["memberName"]
            isbn = args["ISBN"]
            loanDate = args["loanDate"]
            post_data = {
                "memberName": memberName,
                "ISBN": isbn,
                "loanDate": loanDate
            }
            output, error_code = controller.create_loan(post_data)
            if error_code == 201:
                return {"loanID": output}, error_code
            else:
                return {"error": output}, error_code
        except json.JSONDecodeError as e:
            return {'error': 'Invalid JSON format'}, 415  # Return JSON with error message and HTTP status code 415 (Bad Request)

    def get(self):
        query_params = request.args
        if query_params:
            return controller.get_all_loans(query_params=query_params)
        else:
            # Handle the case where there are no query parameters
            # Call a method in the controller to get all books
            books, error_code = controller.get_all_loans(query_params=None)
            return books, error_code

class loanID(Resource):
    def get(self,loanID):
        loan, error_code = controller.get_loan_by_id(loanID)
        if loan is not None:
            return loan, error_code
        else:
            return {'error': 'Loan not found'}, 404

    def delete(self,loanID):
        loan, error_code = controller.delete_loan(loanID)
        if error_code == 200:
            return {"loanID": loan}, 200
        else:
            return {"error": "Loan not found"}, error_code

api.add_resource(Loans, '/loans')
api.add_resource(loanID, '/loans/<int:loanID>')

if __name__ == '__main__':
    # Define the API routes using Flask
    app.run(host='0.0.0.0', port=8001, debug=True)


