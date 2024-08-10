import urllib3
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
logging.basicConfig(level=logging.DEBUG)
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
            raise ValueError("Email or password not set in environment variables.")

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
                    logger.debug("Fetching existing jobs from the database")
                    cur.execute("""
                        SELECT company, title
                        FROM jobs_jobpost
                        WHERE posted_at >= NOW() - INTERVAL '30 days'
                    """)
                    existing_jobs = cur.fetchall()

                    # Create a set of tuples for existing jobs to check against
                    existing_jobs_set = {(row[0], row[1]) for row in existing_jobs}

                    logger.debug(f"Existing jobs in the database: {len(existing_jobs_set)}")

                    # Prepare the data to be inserted, filtering out existing jobs within 30 days
                    values = []
                    for _, row in df.iterrows():
                        title = row.get('vacancy', '')
                        company = row.get('company', '')

                        logger.debug(f"Processing job: {title} at {company}")

                        # Skip rows where necessary data is missing
                        if not title or not company:
                            logger.debug(f"Skipping job with missing data: {title} at {company}")
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
                                    row.get('apply_link', '')[:1000]
                                )
                            )
                            logger.debug(f"Job added for insertion: {title} at {company}")

                    if values:
                        logger.debug(f"Inserting {len(values)} new job posts into the database")
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
            parse_djinni_co = await self.parse_djinni_co(session)

            if not parse_djinni_co.empty:
                self.data = parse_djinni_co
                self.data['scrape_date'] = datetime.now()

                # Drop rows with NaN values in critical columns
                self.data.dropna(subset=['company', 'vacancy'], inplace=True)
            else:
                logger.warning("No jobs scraped from djinni.co")

    async def parse_djinni_co(self, session):
        pages = 15
        logger.info(f"Started scraping djinni.co for the first {pages} pages")

        base_jobs_url = 'https://djinni.co/jobs/'

        jobs = []

        async def scrape_jobs_page(page_url):
            async with session.get(page_url) as response:
                page_response = await response.text()
                soup = BeautifulSoup(page_response, 'html.parser')
                job_items = soup.select('ul.list-unstyled.list-jobs > li')
                for job_item in job_items:
                    job = {}

                    # Extracting company name
                    company_tag = job_item.find('a', class_='text-body')
                    if company_tag:
                        job['company'] = company_tag.text.strip()

                    # Extracting job title
                    title_tag = job_item.find('a', class_='job-item__title-link')
                    if title_tag:
                        job['vacancy'] = title_tag.text.strip()

                    # Extracting application link
                    if title_tag:
                        job['apply_link'] = 'https://djinni.co' + title_tag['href']

                    logger.debug(f"Scraped job: {job}")
                    jobs.append(job)

        # Scrape each page asynchronously
        tasks = []
        for page in range(1, pages + 1):
            logger.info(f"Scraping page {page} for djinni.co")
            page_url = f"{base_jobs_url}?page={page}"
            tasks.append(scrape_jobs_page(page_url))

        await asyncio.gather(*tasks)

        df = pd.DataFrame(jobs, columns=['company', 'vacancy', 'apply_link'])
        logger.info("Scraping completed for djinni.co")

        if df.empty:
            logger.warning("No jobs found during scraping.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

        for job in df.to_dict('records'):
            logger.debug(f"Title: {job['vacancy']}, Company: {job['company']}, Apply Link: {job['apply_link']}")
            logger.info("=" * 40)

        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

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
