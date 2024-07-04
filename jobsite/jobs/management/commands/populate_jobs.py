# jobs/management/commands/populate_jobs.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from jobs.models import JobPost, JobApplication
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Populates the database with fake job posts and applications'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        # Create fake HR users
        hr_users = []
        for _ in range(5):
            hr_user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password123'
            )
            hr_users.append(hr_user)

        # Create fake job posts
        for _ in range(20):
            job = JobPost.objects.create(
                title=fake.job(),
                description=fake.text(),
                company=fake.company(),
                location=fake.city(),
                posted_by=random.choice(hr_users),
                posted_at=fake.date_time_this_year()
            )

        # Create fake applicants
        applicant_users = []
        for _ in range(10):
            applicant_user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password123'
            )
            applicant_users.append(applicant_user)

        # Create fake job applications
        job_posts = JobPost.objects.all()
        for job in job_posts:
            for _ in range(random.randint(1, 5)):
                JobApplication.objects.create(
                    job=job,
                    applicant=random.choice(applicant_users),
                    resume=fake.file_name(extension='pdf'),
                    cover_letter=fake.text(),
                    applied_at=fake.date_time_this_year()
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with fake job posts and applications'))
