import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
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

    async def fetch_url_async(self, url, session, params=None, verify_ssl=True):
        """ Asynchronously fetch the content of a URL. """
        try:
            async with session.get(url, params=params, ssl=verify_ssl) as response:
                response.raise_for_status()
                if response.headers.get('Content-Type') == 'application/json':
                    return await response.json()
                else:
                    return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Request to {url} failed: {e}")
            return None

    def save_to_db(self, df, batch_size=100):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT company, title
                        FROM jobs_jobpost
                        WHERE posted_at >= NOW() - INTERVAL '30 days'
                    """)
                    existing_jobs = cur.fetchall()

                    # Create a set of tuples for existing jobs to check against
                    existing_jobs_set = {(row[0], row[1]) for row in existing_jobs}

                    # Prepare the data to be inserted, filtering out existing jobs within 30 days
                    values = []
                    for _, row in df.iterrows():
                        title = row.get('Job Title', '')
                        company = row.get('Company Name', '')

                        # Skip rows where necessary data is missing
                        if not title or not company:
                            continue

                        if (company, title) not in existing_jobs_set:
                            values.append(
                                (
                                    title[:500],
                                    '',  # Description left blank for now
                                    company[:500],
                                    '',  # Location left blank
                                    None,  # Function left blank
                                    None,  # Schedule left blank
                                    None,  # Deadline left blank
                                    None,  # Responsibilities left blank
                                    None,  # Requirements left blank
                                    9,  # posted_by_id is 9
                                    True,  # is_scraped
                                    False,  # is_premium
                                    0,  # premium_days
                                    99,  # priority_level
                                    datetime.now(),  # current datetime as posted_at
                                    False,  # deleted
                                    row.get('Job Apply Link', '')[:1000]
                                )
                            )

                    if values:
                        insert_query = sql.SQL("""
                            INSERT INTO jobs_jobpost (title, description, company, location, function, schedule, deadline, responsibilities, requirements, posted_by_id, is_scraped, is_premium, premium_days, priority_level, posted_at, deleted, apply_link)
                            VALUES %s
                            ON CONFLICT (company, title) DO NOTHING
                        """)
                        extras.execute_values(cur, insert_query, values, page_size=batch_size)
                        conn.commit()
                        logger.info(f"{len(values)} new job posts inserted into the database.")
                    else:
                        logger.info("No new job posts to insert.")

        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error saving data to the database: {error}")


    async def get_data_async(self):
        async with aiohttp.ClientSession() as session:
            # Fetch data concurrently
            parse_glorri = await self.parse_glorri(session)
            azercell_jobs = await self.parse_azercell(session)
            parse_azerconnect = await self.parse_azerconnect(session)

            # Initialize an empty list to hold all job records
            all_jobs = []

            # Append each set of jobs to the list if it's not empty
            if parse_glorri:
                all_jobs.extend(parse_glorri)
            if not azercell_jobs.empty:
                all_jobs.extend(azercell_jobs.to_dict('records'))
            if not parse_azerconnect.empty:
                all_jobs.extend(parse_azerconnect.to_dict('records'))

            # If we have jobs, convert to a DataFrame
            if all_jobs:
                self.data = pd.DataFrame(all_jobs)
                self.data['scrape_date'] = datetime.now()

                # Drop rows with NaN values in critical columns
                self.data.dropna(subset=['Company Name', 'Job Title'], inplace=True)

    async def parse_glorri(self, session):
        """Fetch all companies and their job data from Glorri."""
        url_companies = "https://atsapp.glorri.az/company-service/v2/companies/public"
        limit = 18
        offset = 0
        total_count = 67
        all_jobs = []

        while offset < total_count:
            params = {'limit': limit, 'offset': offset}
            companies_data = await self.fetch_url_async(url_companies, session, params=params)
            if companies_data:
                companies = companies_data.get('entities', [])
                for company in companies:
                    slug = company.get('slug')
                    company_name = company.get('name')
                    job_count = company.get('jobCount')

                    if job_count > 0 and slug:
                        base_url_jobs = f"https://atsapp.glorri.az/job-service/v2/company/{slug}/jobs"
                        job_offset = 0

                        while True:
                            job_params = {'offset': job_offset, 'limit': limit}
                            jobs_data = await self.fetch_url_async(base_url_jobs, session, params=job_params)
                            if jobs_data:
                                jobs = jobs_data.get('entities', [])
                                if not jobs:
                                    break
                                for job in jobs:
                                    all_jobs.append({
                                        'Company Name': company_name,
                                        'Company Slug': slug,
                                        'Job Title': job['title'],
                                        'Job Apply Link': f"https://jobs.glorri.az/vacancies/{slug}/{job['slug']}/apply"
                                    })
                                job_offset += limit
                            else:
                                logger.error(f"Failed to retrieve jobs for {company_name}.")
                                break

                offset += limit
            else:
                logger.error(f"Failed to retrieve companies data.")
                break

        return all_jobs

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


def main():
    job_scraper = JobScraper()
    asyncio.run(job_scraper.get_data_async())

    if job_scraper.data is None or job_scraper.data.empty:
        logger.warning("No data scraped to save to the database.")
        return

    logger.info(f"Data to be saved: {job_scraper.data}")

    job_scraper.save_to_db(job_scraper.data)

if __name__ == "__main__":
    main()
