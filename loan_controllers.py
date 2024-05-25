import datetime
import requests
from pymongo import MongoClient

class LoanOperations:

    def __init__(self , loanDB, booksDB):
        self.loan_collection = loanDB
        self.book_collection = booksDB
        self.id = 1  # Books ID

    def create_loan(self, data):
        # Extract required data from the POST request
        memberName = data['memberName']
        isbn = data['ISBN']
        loanDate = data['loanDate']
        book_params = {
            'ISBN': isbn
        }
        # Check validity: Missing fields, Wrong ISBN, Too much loans
        book_data = self.get_from_books({'ISBN': isbn})
        print(book_data)
        if not book_data:
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
            'loanID': str(self.id),
            'memberName': memberName,
            'loanDate': loanDate
        }
        self.id += 1
        self.loan_collection.insert_one(new_loan)
        return new_loan['loanID'], 201

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
        return returned_loans, 200

    # Function to get a single loan by ID

    def get_loan_by_id(self, loan_id):
        loan = self.loan_collection.find_one({'loanID': str(loan_id)})
        if loan:
            return loan, 200
        return None, 404


    # Function to delete a loan by ID
    def delete_loan(self, loan_id):
        result = self.loan_collection.delete_one({'loanID': str(loan_id)})
        if result.deleted_count == 1:
            return loan_id, 200
        return None, 404

    def get_from_books(self, query_params=None):
        query = {}
        if query_params:
            query = {key: value for key, value in query_params.items() if value is not None}

        books = list(self.books_collection.find(query))
        if books:
            return books
        return []