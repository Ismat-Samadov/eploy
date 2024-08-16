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
import requests

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

    def fetch_url(self, url, params=None):
        """ Synchronously fetch the content of a URL. """
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
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
                        title = row.get('vacancy', '')
                        company = row.get('company', '')

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
                                    1,  # posted_by_id is 9
                                    True,  # is_scraped
                                    False,  # is_premium
                                    0,  # premium_days
                                    99,  # priority_level
                                    datetime.now(),  # current datetime as posted_at
                                    False,  # deleted
                                    row.get('apply_link', '')[:1000]
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
                        logger.info(values)
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
            parse_djinni_co = await self.parse_djinni_co(session)
            parse_abb = await self.parse_abb(session)
            parse_hellojob_az = await self.parse_hellojob_az(session)
            parse_boss_az = await self.parse_boss_az(session)

            # Initialize an empty list to hold all job records
            all_jobs = []

            # Append each set of jobs to the list if it's not empty
            if parse_glorri:
                all_jobs.extend(parse_glorri)
            if not azercell_jobs.empty:
                all_jobs.extend(azercell_jobs.to_dict('records'))
            if not parse_azerconnect.empty:
                all_jobs.extend(parse_azerconnect.to_dict('records'))
            if not parse_djinni_co.empty:
                all_jobs.extend(parse_djinni_co.to_dict('records'))
            if not parse_abb.empty:
                all_jobs.extend(parse_abb.to_dict('records'))
            if not parse_hellojob_az.empty:
                all_jobs.extend(parse_hellojob_az.to_dict('records'))
            if not parse_boss_az.empty:
                 all_jobs.extend(parse_boss_az.to_dict('records'))

            # If we have jobs, convert to a DataFrame
            if all_jobs:
                self.data = pd.DataFrame(all_jobs)
                self.data['scrape_date'] = datetime.now()

                # Drop rows with NaN values in critical columns
                self.data.dropna(subset=['company', 'vacancy'], inplace=True)

    
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
                                        'company': company_name,
                                        'Company Slug': slug,
                                        'vacancy': job['title'],
                                        'apply_link': f"https://jobs.glorri.az/vacancies/{slug}/{job['slug']}/apply"
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
        for page in range(1, pages + 15):
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
    
    async def parse_abb(self, session):
        logger.info("Scraping starting for ABB")
        base_url = "https://careers.abb-bank.az/api/vacancy/v2/get"
        job_vacancies = []
        page = 0

        while True:
            params = {"page": page}
            response = await self.fetch_url_async(base_url, session, params=params)

            if response:
                try:
                    # Attempt to parse the response as JSON
                    data = response.get("data", [])
                except AttributeError:
                    logger.error("Failed to parse the response as JSON.")
                    break

                if not data:
                    break

                for item in data:
                    title = item.get("title")
                    url = item.get("url")
                    job_vacancies.append({"company": "ABB", "vacancy": title, "apply_link": url})
                page += 1
            else:
                logger.error(f"Failed to retrieve data for page {page}.")
                break

        df = pd.DataFrame(job_vacancies)
        logger.info("ABB scraping completed")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_busy_az(self, session):
        logger.info("Scraping started for busy.az")
        job_vacancies = []
        for page_num in range(1, 5):
            logger.info(f"Scraping page {page_num}")
            url = f'https://busy.az/vacancies?page={page_num}'
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('a', class_='job-listing')

                for job in job_listings:
                    job_details = job.find('div', class_='job-listing-details')
                    job_title = job_details.find('h3', class_='job-listing-title').text.strip()
                    company_element = job_details.find('i', class_='icon-material-outline-business')
                    company_name = company_element.find_parent('li').text.strip() if company_element else 'N/A'
                    apply_link = job.get('href')
                    job_vacancies.append({"company": company_name, "vacancy": job_title, "apply_link": apply_link})
            else:
                logger.error(f"Failed to retrieve page {page_num}.")
        df = pd.DataFrame(job_vacancies)
        logger.info(df)
        logger.info("Scraping completed for busy.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_hellojob_az(self, session):
        logger.info("Started scraping of hellojob.az")
        job_vacancies = []
        base_url = "https://www.hellojob.az"

        for page_number in range(1, 11):
            url = f"{base_url}/vakansiyalar?page={page_number}"
            response = await self.fetch_url_async(url, session)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('a', class_='vacancies__item')
                if not job_listings:
                    logger.info(f"No job listings found on page {page_number}.")
                    continue
                for job in job_listings:
                    company_name = job.find('p', class_='vacancy_item_company').text.strip()
                    vacancy_title = job.find('h3').text.strip()
                    apply_link = job['href'] if job['href'].startswith('http') else base_url + job['href']

                    job_vacancies.append({"company": company_name, "vacancy": vacancy_title, "apply_link": apply_link})
            else:
                logger.warning(f"Failed to retrieve page {page_number}")
        logger.info("Scraping completed for hellojob.az")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(
            columns=['company', 'vacancy', 'apply_link'])

    async def parse_boss_az(self, session):
        logger.info("Starting to scrape Boss.az...")
        job_vacancies = []
        base_url = "https://boss.az"
        
        for page_num in range(1, 21):  # Scrape from page 1 to 20
            url = f"{base_url}/vacancies?page={page_num}"
            response = await self.fetch_url_async(url, session)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('div', class_='results-i')
                for job in job_listings:
                    title = job.find('h3', class_='results-i-title').get_text(strip=True)
                    company = job.find('a', class_='results-i-company').get_text(strip=True)
                    link = f"{base_url}{job.find('a', class_='results-i-link')['href']}"
                    job_vacancies.append({"company": company, "vacancy": title, "apply_link": link})
                logger.info(f"Scraped {len(job_listings)} jobs from page {page_num}")
            else:
                logger.warning(f"Failed to retrieve page {page_num}.")
        
        logger.info("Scraping completed for Boss.az")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(
            columns=['company', 'vacancy', 'apply_link'])


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
