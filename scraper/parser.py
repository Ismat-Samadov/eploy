import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime
import concurrent.futures
from dotenv import load_dotenv
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2 import sql, extras
import aiohttp
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JobScraper:
    def __init__(self):
        self.data = None
        self.load_credentials()
        self.db_params = self.load_db_credentials()
        self.engine = self.create_engine()

    def load_credentials(self):
        load_dotenv()
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        if not self.email or not self.password:
            logger.error("Email or password not set in environment variables.")

    def load_db_credentials(self):
        load_dotenv()
        return {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }

    def create_engine(self):
        db_url = f"postgresql+psycopg2://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['dbname']}"
        return create_engine(db_url)

    async def fetch_url_async(self, url, session, verify_ssl=True):
        """ Asynchronously fetch the content of a URL. """
        try:
            async with session.get(url, ssl=verify_ssl) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Request to {url} failed: {e}")
            return None

    async def parse_azercell(self, session):
        logger.info("Started scraping Azercell")
        url = "https://www.azercell.com/az/about-us/career.html"
        response_text = await self.fetch_url_async(url, session)
        if response_text:
            soup = BeautifulSoup(response_text, "html.parser")
            vacancies_section = soup.find("section", class_="section_vacancies")
            if vacancies_section:
                job_listings = vacancies_section.find_all("a", class_="vacancies__link")
                job_titles = [job.find("h4", class_="vacancies__name").text for job in job_listings]
                job_locations = [job.find("span", class_="vacancies__location").text.strip() for job in job_listings]
                job_links = [job["href"] for job in job_listings]

                # Asynchronously fetch additional details from individual job pages
                tasks = [self.fetch_url_async(urljoin(url, link), session) for link in job_links]
                job_pages = await asyncio.gather(*tasks)

                responsibilities, requirements, functions, schedules, deadlines = [], [], [], [], []

                for job_page in job_pages:
                    if job_page:
                        job_soup = BeautifulSoup(job_page, "html.parser")
                        responsibilities_text = job_soup.find("div", class_="responsibilities").text if job_soup.find("div", class_="responsibilities") else None
                        requirements_text = job_soup.find("div", class_="requirements").text if job_soup.find("div", class_="requirements") else None
                        function_text = job_soup.find("span", class_="function").text if job_soup.find("span", class_="function") else None
                        schedule_text = job_soup.find("span", class_="schedule").text if job_soup.find("span", class_="schedule") else None
                        deadline_text = job_soup.find("span", class_="deadline").text if job_soup.find("span", class_="deadline") else None

                        responsibilities.append(responsibilities_text.strip() if responsibilities_text else None)
                        requirements.append(requirements_text.strip() if requirements_text else None)
                        functions.append(function_text.strip() if function_text else None)
                        schedules.append(schedule_text.strip() if schedule_text else None)
                        deadlines.append(deadline_text.strip() if deadline_text else None)

                df = pd.DataFrame({
                    'company': 'azercell',
                    "vacancy": job_titles,
                    "location": job_locations,
                    "apply_link": job_links,
                    "function": functions,
                    "schedule": schedules,
                    "deadline": deadlines,
                    "responsibilities": responsibilities,
                    "requirements": requirements
                })

                logger.info("Scraping completed for Azercell")
                return df
            else:
                logger.warning("Vacancies section not found on the Azercell page.")
        return pd.DataFrame(columns=['company', 'vacancy', 'location', 'apply_link', 'function', 'schedule', 'deadline', 'responsibilities', 'requirements'])

    async def parse_pashabank(self, session):
        logger.info("Scraping Pashabank")
        url = "https://careers.pashabank.az/az/page/vakansiyalar?q=&branch="
        response_text = await self.fetch_url_async(url, session)

        if response_text:
            soup = BeautifulSoup(response_text, 'html.parser')

            # Find all job listing items
            job_listings = soup.find_all('div', class_='what-we-do-item')

            # Extract job details: vacancy, location, and apply link
            vacancy_list = [listing.find('h3').text.strip() for listing in job_listings]
            location_list = [listing.find('span').text.strip() for listing in job_listings]
            apply_link_list = [listing.find('a')['href'].strip() for listing in job_listings]

            # Asynchronously fetch additional details from job pages
            tasks = [self.fetch_url_async(urljoin(url, link), session) for link in apply_link_list]
            job_pages = await asyncio.gather(*tasks)

            responsibilities, requirements, functions, schedules, deadlines = [], [], [], [], []

            for job_page in job_pages:
                if job_page:
                    job_soup = BeautifulSoup(job_page, "html.parser")
                    responsibilities_text = job_soup.find("div", class_="responsibilities").text if job_soup.find("div", class_="responsibilities") else None
                    requirements_text = job_soup.find("div", class_="requirements").text if job_soup.find("div", class_="requirements") else None
                    function_text = job_soup.find("span", class_="function").text if job_soup.find("span", class_="function") else None
                    schedule_text = job_soup.find("span", class_="schedule").text if job_soup.find("span", class_="schedule") else None
                    deadline_text = job_soup.find("span", class_="deadline").text if job_soup.find("span", class_="deadline") else None

                    responsibilities.append(responsibilities_text.strip() if responsibilities_text else None)
                    requirements.append(requirements_text.strip() if requirements_text else None)
                    functions.append(function_text.strip() if function_text else None)
                    schedules.append(schedule_text.strip() if schedule_text else None)
                    deadlines.append(deadline_text.strip() if deadline_text else None)

            # Ensure all lists are of the same length
            max_len = max(len(vacancy_list), len(location_list), len(apply_link_list), len(responsibilities),
                          len(requirements), len(functions), len(schedules), len(deadlines))
            vacancy_list += [None] * (max_len - len(vacancy_list))
            location_list += [None] * (max_len - len(location_list))
            apply_link_list += [None] * (max_len - len(apply_link_list))
            responsibilities += [None] * (max_len - len(responsibilities))
            requirements += [None] * (max_len - len(requirements))
            functions += [None] * (max_len - len(functions))
            schedules += [None] * (max_len - len(schedules))
            deadlines += [None] * (max_len - len(deadlines))

            # Create DataFrame with the extracted data
            df = pd.DataFrame({
                'company': 'pashabank',
                'vacancy': vacancy_list,
                'location': location_list,
                'apply_link': apply_link_list,
                'function': functions,
                'schedule': schedules,
                'deadline': deadlines,
                'responsibilities': responsibilities,
                'requirements': requirements
            })

            # Remove any duplicates based on 'company', 'vacancy', 'location', and 'apply_link'
            df = df.drop_duplicates(subset=['company', 'vacancy', 'location', 'apply_link'])

            logger.info("Pashabank Scraping completed")
            return df

        # Return an empty DataFrame if scraping fails
        return pd.DataFrame(columns=['company', 'vacancy', 'location', 'apply_link', 'function', 'schedule', 'deadline', 'responsibilities', 'requirements'])

    async def parse_azerconnect(self, session):
        logger.info("Started scraping Azerconnect")
        url = "https://www.azerconnect.az/vacancies"
        response_text = await self.fetch_url_async(url, session, verify_ssl=False)

        if response_text:
            soup = BeautifulSoup(response_text, 'html.parser')
            job_listings = soup.find_all('div', class_='CollapsibleItem_item__CB3bC')

            jobs_data = []

            for job in job_listings:
                title_elem = job.find('div', class_='CollapsibleItem_toggle__XNu5y').find('span')
                if title_elem:
                    title = title_elem.text.strip()
                else:
                    title = "No Title"

                # Extract the content block
                content_block = job.find('div', class_='CollapsibleItem_contentInner__vVcvk')

                # Extract fields from the content block
                function, schedule, deadline, responsibilities, requirements = "", "", "", "", ""

                # Extract the specific sections
                details = content_block.find_all('p')
                for detail in details:
                    text = detail.get_text(strip=True)
                    if text.startswith("Funksiya:"):
                        function = text.replace("Funksiya:", "").strip()
                    elif text.startswith("İdarə:"):
                        function = text.replace("İdarə:", "").strip()
                    elif text.startswith("İş qrafiki:"):
                        schedule = text.replace("İş qrafiki:", "").strip()
                    elif text.startswith("Son müraciət tarixi:"):
                        deadline = text.replace("Son müraciət tarixi:", "").strip()
                    elif text.startswith("Vəzifənin tələbləri:"):
                        requirements = text.replace("Vəzifənin tələbləri:", "").strip()
                    elif text.startswith("Sizin vəzifə öhdəlikləriniz:") or text.startswith("Əlavə Dəyərli Xidmətlər əməliyyatları üzrə ekspert olaraq sizin vəzifə öhdəlikləriniz:"):
                        responsibilities = text.replace("Sizin vəzifə öhdəlikləriniz:", "").strip()

                # Extract unordered list (ul) sections
                uls = content_block.find_all('ul')
                if uls:
                    for ul in uls:
                        if "Vəzifənin tələbləri" in ul.previous_sibling.get_text(strip=True):
                            requirements += '\n' + '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])
                        elif "Sizin əsas vəzifə öhdəlikləriniz" in ul.previous_sibling.get_text(strip=True):
                            responsibilities += '\n' + '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])

                # Extract the apply link
                apply_link_elem = job.find('a', class_='Button_button-blue__0wZ4l')
                if apply_link_elem:
                    apply_link = apply_link_elem['href']
                else:
                    apply_link = "No Apply Link"

                # Parse the deadline into a valid date format
                if deadline:
                    try:
                        # Handle different date formats
                        if '.' in deadline:
                            deadline_date = datetime.strptime(deadline, "%d.%m.%Y").date()
                        else:
                            deadline_date = datetime.strptime(deadline, "%d %B %Y").date()
                    except ValueError:
                        deadline_date = None
                else:
                    deadline_date = None

                job_data = {
                    'company': 'azerconnect',
                    'vacancy': title,
                    'location': 'Baku, Azerbaijan',
                    'function': function,
                    'schedule': schedule,
                    'deadline': deadline_date,
                    'responsibilities': responsibilities,
                    'requirements': requirements,
                    'apply_link': apply_link
                }

                jobs_data.append(job_data)

            df = pd.DataFrame(jobs_data)
            logger.info("Scraping of Azerconnect completed")
            return df

        return pd.DataFrame(columns=['company', 'vacancy', 'location', 'function', 'schedule', 'deadline', 'responsibilities', 'requirements', 'apply_link'])

    async def get_data_async(self):
        async with aiohttp.ClientSession() as session:
            # Execute all parse methods concurrently
            results = await asyncio.gather(
                self.parse_azercell(session),
                self.parse_pashabank(session),
                self.parse_azerconnect(session)
            )
            self.data = pd.concat(results, ignore_index=True)
            self.data['scrape_date'] = datetime.now()

    def save_to_db(self, df, batch_size=100):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT company, title, apply_link
                        FROM jobs_jobpost
                        WHERE posted_at >= NOW() - INTERVAL '30 days'
                    """)
                    existing_jobs = cur.fetchall()

                    # Create a set of tuples for existing jobs to check against
                    existing_jobs_set = {(row[0], row[1], row[2]) for row in existing_jobs}

                    # Prepare the data to be inserted, filtering out existing jobs within 30 days
                    values = [
                        (
                            row['vacancy'][:500],
                            '',  # Description left blank for now
                            row['company'][:500],
                            row['location'][:500],
                            row['function'][:500] if row['function'] else None,
                            row['schedule'][:500] if row['schedule'] else None,
                            row['deadline'],  # Use the date object directly
                            row['responsibilities'] if row['responsibilities'] else None,
                            row['requirements'] if row['requirements'] else None,
                            9,  # assuming posted_by_id is 1
                            True,  # is_scraped
                            False,  # is_premium
                            0,  # premium_days
                            99,  # priority_level
                            datetime.now(),  # current datetime as posted_at
                            False,  # deleted
                            row['apply_link'][:1000]
                        )
                        for _, row in df.iterrows()
                        if (row['company'], row['vacancy'], row['apply_link']) not in existing_jobs_set
                    ]

                    if values:
                        insert_query = sql.SQL("""
                            INSERT INTO jobs_jobpost (title, description, company, location, function, schedule, deadline, responsibilities, requirements, posted_by_id, is_scraped, is_premium, premium_days, priority_level, posted_at, deleted, apply_link)
                            VALUES %s
                            ON CONFLICT (company, title, apply_link) DO NOTHING
                        """)
                        extras.execute_values(cur, insert_query, values, page_size=batch_size)
                        conn.commit()
                        logger.info(f"{len(values)} new job posts inserted into the database.")
                    else:
                        logger.info("No new job posts to insert.")

        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error saving data to the database: {error}")


def main():
    job_scraper = JobScraper()
    asyncio.run(job_scraper.get_data_async())

    if job_scraper.data.empty:
        logger.warning("No data scraped to save to the database.")
        return

    logger.info(f"Data to be saved: {job_scraper.data}")

    job_scraper.save_to_db(job_scraper.data)


if __name__ == "__main__":
    main()
