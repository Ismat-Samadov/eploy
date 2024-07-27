### CareerHorizon

CareerHorizon is a Django-based job posting website where employees can apply for jobs and HRs can post jobs.

## Features

- HRs can post job listings
- Employees can view and apply for jobs
- Admin interface to manage job postings and applications
- Secure and scalable database using PostgreSQL

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Ismat-Samadov/CareerHorizon.git
    cd CareerHorizon
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up the environment variables by creating a `.env` file in the root directory and adding your credentials:
    ```dotenv
    DATABASE_URL=your-database-url
    SECRET_KEY=your-secret-key
    DEBUG=True
    GS_BUCKET_NAME=your-bucket-name
    GCS_TYPE=service_account
    GCS_PROJECT_ID=your-project-id
    GCS_PRIVATE_KEY_ID=your-private-key-id
    GCS_PRIVATE_KEY="your-private-key"
    GCS_CLIENT_EMAIL=your-client-email
    GCS_CLIENT_ID=your-client-id
    GCS_AUTH_URI=https://accounts.google.com/o/oauth2/auth
    GCS_TOKEN_URI=https://oauth2.googleapis.com/token
    GCS_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
    GCS_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-client-email
    ACCESS_TOKEN=your-access-token
    OPENAI_API_KEY=your-openai-api-key
    DJANGO_SETTINGS_MODULE=jobsite.settings
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.office365.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_USE_SSL=False
    EMAIL_HOST_USER=your-email
    EMAIL_HOST_PASSWORD=your-email-password
    DEFAULT_FROM_EMAIL=your-email
    ```

5. Run the initial migrations:
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

6. Create a superuser to access the Django admin:
    ```sh
    python manage.py createsuperuser
    ```

7. Start the development server:
    ```sh
    python manage.py runserver
    ```

8. Access the application at `http://127.0.0.1:8000/` and the admin interface at `http://127.0.0.1:8000/admin/`.

## Usage

- HRs can log in to the admin interface to post job listings.
- Employees can view the job listings and apply for jobs directly from the website.

## Populating the Database with Fake Data

To populate the database with fake job postings and applications for testing purposes, you can use the custom management command provided:

```sh
python manage.py populate_jobs
```

This will create fake HR users, job posts, and applications.

## Project Structure

- `jobsite/` - Main project directory
- `jobs/` - App directory containing models, views, forms, and templates
- `templates/` - HTML templates for the project
- `static/` - Static files (CSS, JavaScript, Images)
- `media/` - Media files (uploads)

## Diagram

```plaintext
+-------------------+        +-------------------+        +-------------------+
|    Frontend       |        |      Backend      |        |      Database     |
+-------------------+        +-------------------+        +-------------------+
| - HTML/CSS        |        |                   |        |                   |
| - Bootstrap       |        | - Django Views    |        | - PostgreSQL      |
| - JavaScript      |        |                   |        |                   |
+---------+---------+        +---------+---------+        +---------+---------+
          |                          |                          |
          |                          |                          |
          |  HTTP Requests           |  Process Requests        |
          |                          |  & Interact with DB      |
          |                          |                          |
          v                          v                          v
+-------------------+        +-------------------+        +-------------------+
|                   |        |                   |        |                   |
|    Templates      |        |      Views        |        |      Models       |
|                   |        |                   |        |                   |
+-------------------+        +-------------------+        +-------------------+
| - base.html       |        | - job_list        |        | - CustomUser      |
| - register.html   |        | - post_job        |        | - JobPost         |
| - login.html      |        | - apply_job       |        | - JobApplication  |
| - job_list.html   |        | - job_applicants  |        |                   |
| - post_job.html   |        | - edit_job        |        |                   |
+-------------------+        +-------------------+        +-------------------+
          |                          |                          |
          |  Render HTML             |  Handle Logic            |  Store Data  |
          |                          |                          |
          v                          v                          v
+-------------------+        +-------------------+        +-------------------+
|   URL Routing     |        |                   |        |                   |
+-------------------+        +-------------------+        +-------------------+
| - urls.py         |        |  - forms.py       |        |  - models.py      |
+-------------------+        +-------------------+        +-------------------+
| - jobs/urls.py    |        | - CustomUserForm  |        | - CustomUser      |
| - users/urls.py   |        | - JobPostForm     |        | - JobPost         |
+-------------------+        +-------------------+        +-------------------+
          |                          |                          |
          |                          |                          |
          v                          v                          v
+-------------------+        +-------------------+        +-------------------+
|                   |        |                   |        |                   |
|  Authentication   |        |  Business Logic   |        |  Data Storage     |
+-------------------+        +-------------------+        +-------------------+
| - Login/Logout    |        | - Handle Forms    |        | - Store User Data |
| - Register User   |        | - Validate Input  |        | - Store Job Data  |
| - User Roles      |        | - Query Database  |        | - Store Apps Data |
+-------------------+        +-------------------+        +-------------------+
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a pull request