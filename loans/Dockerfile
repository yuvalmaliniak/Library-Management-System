FROM python:3.12.2-slim as base
WORKDIR /app
COPY loan_controllers.py .
COPY loan_main.py .
RUN pip install flask
RUN pip install flask_restful
RUN pip install requests
RUN pip install bson
RUN pip install pymongo
RUN pip install datetime
EXPOSE 8001
CMD ["python3", "loan_main.py"]