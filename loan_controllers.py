import datetime
import requests
from pymongo import MongoClient

class LoanOperations:

    def __init__(self , loanDB):
        self.loan_collection = loanDB
        self.id = self.get_highest_id()  # Books ID

    def get_highest_id(self):
        # Check if the collection is empty
        if self.loan_collection.count_documents({}) == 0:
            return 1
        
        # Retrieve all documents
        all_documents = self.loan_collection.find()
        # Convert the id field to an integer and find the highest id
        highest_id = 0
        for doc in all_documents: 
                current_id = int(doc['loanID'])
                if current_id > highest_id:
                    highest_id = current_id
        return highest_id+1

    def create_loan(self, data):
        # Extract required data from the POST request
        memberName = data['memberName']
        isbn = data['ISBN']
        loanDate = data['loanDate']
        # Check validity: Missing fields, Wrong ISBN, Too much loans
        book_data,error_code = self.get_from_books({'ISBN': isbn})
        print(book_data)
        if error_code != 200 or len(book_data) == 0:
            error_message = f"Sorry {memberName}, the ISBN is not in the library"
            return error_message, 422

        num_of_loans = self.loan_collection.count_documents({'memberName': memberName})
        if num_of_loans >= 2:
            error_message = f"Sorry {memberName}, you already have 2 or more books on loan"
            return error_message, 422

        loan_exists = self.loan_collection.find_one({'ISBN': isbn})
        if loan_exists:
            error_message = f"Sorry {memberName}, the book is already on loan"
            return error_message, 422

        # Enter data into the new loan
        new_loan = {
            'title': book_data[0]['title'],
            'ISBN': isbn,
            'bookID': book_data[0]['id'],
            'loanID': str(self.id),  # You might want to use ObjectId for MongoDB IDs
            'memberName': memberName,
            'loanDate': loanDate
        }
        self.id += 1
        self.loan_collection.insert_one(new_loan)
        return new_loan['loanID'], 201
    
    def convert_objectid(self, obj):
        for item in obj:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        print(obj)
        return obj

    # Function to get all loans
    def get_all_loans(self, query_params=None):
        returned_loans = []
        if query_params:
            books, error_code = self.get_from_books(query_params)
            if error_code == 200:
                book_ids = [book['id'] for book in books]
                print(book_ids)
                returned_loans = list(self.loan_collection.find({'bookID': {'$in': book_ids}}))
        else:
            returned_loans = list(self.loan_collection.find())
        returned_loans = self.convert_objectid(returned_loans)
        return returned_loans, 200

    # Function to get a single loan by ID
    def get_loan_by_id(self, loan_id):
        loan = self.loan_collection.find_one({'loanID': str(loan_id)})
        if loan:
            loan['_id']= str(loan['_id'])
            return loan, 200
        return None, 404


    # Function to delete a loan by ID
    def delete_loan(self, loan_id):
        result = self.loan_collection.delete_one({'loanID': str(loan_id)})
        if result.deleted_count == 1:
            return loan_id, 200
        return None, 404

    def get_from_books(self, query_params=None):
        url = "http://localhost:8000/books"

        try:
            if query_params is not None:
                response = requests.get(url, params=query_params)
            else:
                response = requests.get(url)

            response.raise_for_status()
            books = response.json()

            return books, 200

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {"error": "An error occurred while fetching books"}, 422