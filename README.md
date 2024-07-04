# CareerHorizon

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
    SECRET_KEY=your-secret-key
    DEBUG=True
    DATABASE_NAME=your-database-name
    DATABASE_USER=your-database-user
    DATABASE_PASSWORD=your-database-password
    DATABASE_HOST=your-database-host
    DATABASE_PORT=your-database-port
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

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a pull request
