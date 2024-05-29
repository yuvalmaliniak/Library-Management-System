FROM python:3.12.2-slim as base
WORKDIR /app
COPY book_controllers.py .
COPY book_main.py .
RUN pip install flask
RUN pip install flask_restful
RUN pip install requests
RUN pip install bson
RUN pip install pymongo
RUN pip install datetime
EXPOSE 8000
CMD ["python3", "book_main.py"]