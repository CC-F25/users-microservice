# users-microservice

# Program Description
Users Microservice

# Installation

- python 3.10+
- create a venv or conda environment
- `pip install requirements.txt`

# Program Execution

when using conda .env
`python .\main.py`

alternatively-
`uvicorn main:app --reload`

# Models and the CRUD Operations:

1) Health (default)
2) Users

## All models have:
i. **GET** `/<resource>`  
ii. **POST** `/<resource>`  
iii. **GET** `/<resource>/{id}`  
iv. **PUT** `/<resource>/{id}`  
v. **DELETE** `/<resource>/{id}`  
