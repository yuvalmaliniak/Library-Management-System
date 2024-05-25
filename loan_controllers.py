import datetime
import requests

genre_values = ['Fiction', 'Children', 'Biography', 'Science', 'Science Fiction', 'Fantasy', 'Other']


class LoanOperations:
    loan_data = []  # Temporary data storage (list of dictionaries)

    def __init__(self):
        self.id = 1  # Books ID

    def create_loan(self, data):
        # Extract required data from the POST request
        memberName = data['memberName']
        isbn = data['ISBN']
        loanDate = data['loanDate']
        book_json = {
            'ISBN': isbn
        }
        # Check validity: Missing fields, Wrong ISBN, Too much loans
        book_data, error_code = self.get_from_books("GET", book_json)
        if error_code != 200:
            error_message = f"Sorry {memberName},  the ISBN is not in the library"
            return error_message, 422
        num_of_loans = 0
        for loan in self.loan_data:
            if loan['ISBN'] == isbn:
                error_message = f"Sorry {memberName}, The book is already on loan"
                return error_message, 422
            if loan['memberName'] == memberName:
                num_of_loans += 1
        if num_of_loans >= 2:
            error_message = f"Sorry {memberName},  You already have 2 or more books on loan"
            return error_message, 422
        # Enter data into the new loan

        # Get today's date
        today_date = datetime.date.today()
        # Format the date as a string in 'YYYY-MM-DD' format
        formatted_date = today_date.strftime('%Y-%m-%d')
        new_loan = {
            'title': book_data['title'],
            'ISBN': isbn,
            'bookID': book_data['id'],
            'loanID': str(self.id),
            'memberName': memberName,
            'loanDate': str(formatted_date)
        }
        self.id+=1
        self.loan_data.append(new_loan)
        return new_loan['loanID'], 201

    # Function to get all loans
    def get_all_loans(self, query_params=None):
        returned_loans = []
        if query_params:
            books, error_code = self.get_from_books("GET", query_params)
            if error_code == 200:
                book_ids = [book['id'] for book in books]
                returned_loans = [loan for loan in self.loan_data if loan['id'] in book_ids]
        else:
            returned_loans = self.loan_data
        return returned_loans, 200

    # Function to get a single loan by ID

    def get_loan_by_id(self,loan_id):
        for loan in self.loan_data:
            if loan['id'] == str(loan_id):
                return loan, 200
        return None, 404
    # Function to get a single book by ID

    # Function to delete a book by ID
    def delete_loan(self, loan_id):
        for i, loan in enumerate(self.loan_data):
            if loan['loanID'] == str(loan_id):
                del self.loan_data[i]
                return loan['loanID'], 200
        # No book found, return 404 error code
        return None, 404
    def get_from_books(self, method, params):
        # Define the base URL
        #url = "http://books-services:8090/books"
        url = "https://localhost:8000/books"
        # Check if the method is GET
        if method.upper() == "GET":
            try:
                # Make the GET request with the provided parameters
                response = requests.get(url, params=params)
                
                # Raise an exception if the request was unsuccessful
                response.raise_for_status()
                
                # Return the JSON response
                return response.json(), 200
            except requests.exceptions.RequestException as e:
                # Handle exceptions (e.g., network problems, invalid responses)
                print(f"An error occurred: {e}")
                return None, 404
        else:
            print("Invalid method. Only 'GET' is supported.")
            return None, 404
        