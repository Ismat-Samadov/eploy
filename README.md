# CareerHorizon

**CareerHorizon** is a Django-based job posting platform where HR professionals can post jobs, and candidates can view and apply for these opportunities. The platform aggregates job listings across various companies and websites in Azerbaijan, offering a centralized location for job seekers.

## Features

- **HR Features:**
  - Post and manage job listings
  - View and download applicants for specific job posts
  - Search and filter job posts
- **Candidate Features:**
  - Browse and apply for job listings
  - Upload resumes for job applications
  - Parse CVs and compare with job descriptions
- **Admin Features:**
  - Manage users, job posts, and applications through Django's admin interface
- **Technology Stack:**
  - Backend: Django, PostgreSQL
  - Frontend: HTML, CSS, Bootstrap, JavaScript
  - File Storage: DigitalOcean Spaces

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/Ismat-Samadov/CareerHorizon.git
    cd CareerHorizon
    ```

2. **Create a virtual environment and activate it:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

3. **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the environment variables by creating a `.env` file:**
    ```dotenv
    DATABASE_URL=your-database-url
    SECRET_KEY=your-secret-key
    DEBUG=True
    # Add other environment variables as needed...
    ```

5. **Run the initial migrations:**
    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

6. **Create a superuser to access the Django admin:**
    ```sh
    python manage.py createsuperuser
    ```

7. **Start the development server:**
    ```sh
    python manage.py runserver
    ```

8. **Access the application:**
   - Application: `http://127.0.0.1:8000/`
   - Admin interface: `http://127.0.0.1:8000/admin/`

## Usage

- **HR Users:**
  - Log in to post jobs, view job applications, and download applicant data as Excel files.
- **Candidates:**
  - Browse job listings, apply to jobs, and upload resumes.

## Populating the Database

For testing purposes, you can populate the database with fake data:

```sh
python manage.py populate_jobs
```

## Project Structure

```plaintext
CareerHorizon/
├── jobsite/                # Main project directory
├── jobs/                   # App directory for jobs functionality
│   ├── models.py           # Models for JobPost, JobApplication, etc.
│   ├── views.py            # Views for job listings, applications, etc.
│   ├── forms.py            # Forms for creating/editing jobs and applications
│   ├── urls.py             # URL routing for jobs app
│   ├── templates/          # HTML templates
│   └── static/             # Static files (CSS, JavaScript, Images)
└── users/                  # App directory for user management
    ├── models.py           # CustomUser model with roles
    ├── views.py            # Views for user registration, login, etc.
    ├── forms.py            # Forms for user registration, login, etc.
    ├── urls.py             # URL routing for users app
    ├── templates/          # HTML templates
    └── static/             # Static files (CSS, JavaScript, Images)
```

## Diagram Flow

```plaintext
+-------------------+         +-------------------+         +-------------------+
|    Frontend       |         |      Backend      |         |      Database     |
+-------------------+         +-------------------+         +-------------------+
| - HTML/CSS        |  <----> | - Django Views    |  <----> | - PostgreSQL      |
| - Bootstrap       |         | - Models          |         |                   |
| - JavaScript      |         | - Forms           |         |                   |
+---------+---------+         +---------+---------+         +---------+---------+
          |                             |                             |
          | HTTP Requests               | Process Requests            |
          |                             | Interact with Database       |
          v                             v                             v
+-------------------+         +-------------------+         +-------------------+
|    Templates      |         |      Views        |         |      Models       |
+-------------------+         +-------------------+         +-------------------+
| - base.html       |  <----> | - job_list        |  <----> | - CustomUser      |
| - register.html   |         | - post_job        |         | - JobPost         |
| - login.html      |         | - apply_job       |         | - JobApplication  |
| - job_list.html   |         | - download_xlsx   |         |                   |
+-------------------+         +-------------------+         +-------------------+
```

## Contributing

1. **Fork the repository**
2. **Create a new branch** (`git checkout -b feature-branch`)
3. **Commit your changes** (`git commit -m 'Add some feature'`)
4. **Push to the branch** (`git push origin feature-branch`)
5. **Open a pull request**



### Sequence Diagram: Job Posting and Application Flow

```plaintext
Participant 1: HR User
Participant 2: Web Browser
Participant 3: Django Server
Participant 4: PostgreSQL Database
Participant 5: DigitalOcean Spaces

Note: HR User logs into the platform.
HR User -> Web Browser: Log in
Web Browser -> Django Server: HTTP POST /login
Django Server -> PostgreSQL Database: Validate user credentials
PostgreSQL Database -> Django Server: Return user data
Django Server -> Web Browser: Return session cookie

Note: HR User posts a new job.
HR User -> Web Browser: Enter job details
Web Browser -> Django Server: HTTP POST /post_job
Django Server -> PostgreSQL Database: Save job post
Django Server -> Web Browser: Return job post confirmation

Note: Candidate views job listings.
Candidate -> Web Browser: Visit job listings page
Web Browser -> Django Server: HTTP GET /jobs
Django Server -> PostgreSQL Database: Fetch job listings
PostgreSQL Database -> Django Server: Return job data
Django Server -> Web Browser: Render job listings

Note: Candidate applies for a job.
Candidate -> Web Browser: Apply for a job
Web Browser -> Django Server: HTTP POST /apply_job
Web Browser -> DigitalOcean Spaces: Upload resume file
DigitalOcean Spaces -> Web Browser: Return file URL
Django Server -> PostgreSQL Database: Save application data
Django Server -> Web Browser: Return application confirmation

Note: HR User downloads applicant data.
HR User -> Web Browser: Request XLSX download
Web Browser -> Django Server: HTTP GET /download_applicants/<job_id>
Django Server -> PostgreSQL Database: Fetch applicant data
Django Server -> Django Server: Generate XLSX file
Django Server -> Web Browser: Download XLSX file
```

### Explanation of the Sequence Diagram

1. **Login Process:**
   - The HR user logs in by sending their credentials via the web browser to the Django server, which validates them against the PostgreSQL database.
   - Upon successful authentication, a session is established.

2. **Job Posting:**
   - The HR user submits a job post form, which the Django server processes and stores in the PostgreSQL database.
   - The user receives a confirmation of the successful job posting.

3. **Viewing Job Listings:**
   - A candidate visits the job listings page.
   - The Django server queries the PostgreSQL database for job data and renders the listings on the webpage.

4. **Job Application:**
   - The candidate selects a job and applies by submitting their details and uploading a resume.
   - The resume is uploaded to DigitalOcean Spaces, and the URL is stored in the PostgreSQL database along with the application data.

5. **Downloading Applicant Data:**
   - The HR user requests to download applicant data for a specific job post.
   - The Django server queries the database, generates an XLSX file, and sends it to the HR user for download.

This diagram helps visualize the step-by-step process of interaction between users, the web browser, the Django server, and external services like DigitalOcean Spaces and the PostgreSQL database. It can be extended or detailed further to include other parts of the application as needed.
