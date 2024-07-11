# jobs/management/commands/populate_jobs.py

from django.core.management.base import BaseCommand
from users.models import CustomUser  # Update this import
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
            hr_user = CustomUser.objects.create_user(  # Update this to use CustomUser
                username=fake.user_name(),
                email=fake.email(),
                password='password123',
                user_type='HR'
            )
            hr_users.append(hr_user)

        # Create a default user for scraped jobs
        default_user, created = CustomUser.objects.get_or_create(
            username='scraper_user',
            defaults={'email': 'scraper@example.com', 'password': 'password123', 'user_type': 'HR'}
        )

        # Create fake job posts
        job_descriptions = [
            "We are looking for a Java Developer with experience in building high-performing, scalable, enterprise-grade applications. You will be part of a talented software team that works on mission-critical applications. Java developer roles and responsibilities include managing Java/Java EE application development while providing expertise in the full software development lifecycle, from concept and design to testing. Java developer responsibilities include designing, developing and delivering high-volume, low-latency applications for mission-critical systems.",
            "Business analysts are the drivers of our continued growth and success. With their commitment to innovation, these analysts seek, develop, and help implement strategic initiatives for improved efficiency and productivity. We’re currently searching for an experienced business analyst to help guide our organization to the future. From researching progressive systems solutions to evaluating their impacts, the ideal candidate will be a detailed planner, expert communicator, and top-notch analyst.",
            "At CareerHorizon, we’re proud to stand at the forefront of the Big Data revolution. Using the latest analytics tools and processes, we’re able to maximize our offerings and deliver unparalleled service and support. To help carry us even further, we’re searching for an experienced data analyst to join our team. The ideal candidate will be highly skilled in all aspects of data analytics, including mining, generation, and visualization. Additionally, this person should be committed to transforming data into readable, goal-oriented reports that drive innovation and growth.",
            "We are looking for a passionate Python developer to join our team at CareerHorizon. You will be responsible for developing and implementing high-quality software solutions, creating complex applications using cutting-edge programming features and frameworks and collaborating with other teams in the firm to define, design and ship new features. As an active part of our company, you will brainstorm and chalk out solutions to suit our requirements and meet our business goals.",
            "We are looking for a savvy Data Engineer to join our growing team of analytics experts. The hire will be responsible for expanding and optimizing our data and data pipeline architecture, as well as optimizing data flow and collection for cross functional teams. The ideal candidate is an experienced data pipeline builder and data wrangler who enjoys optimizing data systems and building them from the ground up. The Data Engineer will support our software developers, database architects, data analysts and data scientists on data initiatives and will ensure optimal data delivery architecture is consistent throughout ongoing projects.",
            "We are looking for a Data Scientist to analyze large amounts of raw information to find patterns that will help improve our company. We will rely on you to build data products to extract valuable business insights. In this role, you should be highly analytical with a knack for analysis, math and statistics. Critical thinking and problem-solving skills are essential for interpreting data. We also want to see a passion for machine-learning and research.",
            "We are looking for an outstanding Web Developer to be responsible for the coding, innovative design and layout of our website. Web developer responsibilities include building our website from concept all the way to completion from the bottom up, fashioning everything from the home page to site layout and function."
        ]
        
        job_titles = [
            "Java Developer",
            "Business Analyst",
            "Data Analyst",
            "Python Developer",
            "Data Engineer",
            "Data Scientist",
            "Web Developer"
        ]

        # Create fake job posts from website
        for i in range(len(job_titles)):
            job = JobPost.objects.create(
                title=job_titles[i],
                description=job_descriptions[i],
                company="CareerHorizon",
                location="Baku, Azerbaijan",
                posted_by=random.choice(hr_users),
                posted_at=fake.date_time_this_year(),
                is_scraped=False
            )

        # Create fake scraped job posts
        for i in range(len(job_titles)):
            job = JobPost.objects.create(
                title=f"Scraped {job_titles[i]}",
                description=job_descriptions[i],
                company="ScrapedCompany",
                location="Baku, Azerbaijan",
                posted_by=default_user,  # Use the default user
                posted_at=fake.date_time_this_year(),
                is_scraped=True,
                apply_link=fake.url()
            )

        # Create fake applicants
        applicant_users = []
        for _ in range(10):
            applicant_user = CustomUser.objects.create_user(  # Update this to use CustomUser
                username=fake.user_name(),
                email=fake.email(),
                password='password123',
                user_type='Candidate'
            )
            applicant_users.append(applicant_user)

        # Create fake job applications
        job_posts = JobPost.objects.filter(is_scraped=False)
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
