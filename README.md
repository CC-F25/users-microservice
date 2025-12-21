# users-microservice

# Program Description
Users Microservice

An atomic microservice of the bookings platform app.

# Installation

- python 3.10+
- create a venv or conda environment
- `pip install -r requirements.txt`

# Env file-

- rename .sample-env to .env
- fill in the required parameters

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


# Deployment instructions (Cloud Run + Cloud SQL)

0) Both Cloud Run + Cloud SQLservices need to be active
1) Create a Dockerfile
2) Build the New Image
This packages the updated code and sends it to GCP.

Paste in powershell
`gcloud builds submit --tag gcr.io/<\image name>`
(Wait for this to finish and say "SUCCESS")

3) Paste in powershell


```powershell
gcloud run deploy <service-name> `
  --image gcr.io/<project-id>/<image-name> `
  --platform managed `
  --region <region> `
  --allow-unauthenticated `
  --add-cloudsql-instances <project-id>:<region>:<cloudsql-instance-name> `
  --set-env-vars "MYSQL_USER=<mysql-user>" `
  --set-env-vars "MYSQL_PASSWORD=<mysql-password>" `
  --set-env-vars "MYSQL_DB=<mysql-db-name>" `
  --set-env-vars "INSTANCE_CONNECTION_NAME=<project-id>:<region>:<cloudsql-instance-name>" `
  --set-env-vars "JWT_SECRET=<jwt-secret>" `
  --set-env-vars "GOOGLE_CLIENT_ID=<google-client-id>" `
  --set-env-vars "GCP_PROJECT_ID=<gcp-project-id>" `
  --set-env-vars "PUBSUB_TOPIC=<pubsub-topic>"
```

4) Testing connection

How to test:

Go to Cloud Run URL: https://users-microservice-258517926293.us-central1.run.app/test-db

If everything works, you’ll get a JSON response with DB connection status.

Test /test-db again to confirm the new image works


# How the Deployment works-
Setup:

Service deployed on Cloud Run (users-microservice).

Connected to Cloud SQL database (users_db) via Cloud SQL Unix socket.

DB user: users_user (password stored in environment variables).

Includes a test endpoint /test-db to check DB connectivity.

How connection works:

Cloud Run container automatically connects to Cloud SQL through the Unix socket.

No local proxy or direct IP needed – Cloud Run handles the networking securely.

DB credentials are read from environment variables inside the container.
