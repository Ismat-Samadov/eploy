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

    async def fetch_url_async(self, url, session, params=None, headers=None, verify_ssl=True):
        """ Asynchronously fetch the content of a URL with optional headers. """
        try:
            async with session.get(url, params=params, headers=headers, ssl=verify_ssl) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '').lower()

                if 'application/json' in content_type:
                    return await response.json()
                elif 'text' in content_type or 'html' in content_type:
                    try:
                        return await response.text(encoding='utf-8')
                    except UnicodeDecodeError:
                        return await response.text(encoding='latin-1')
                else:
                    logger.error(f"Unexpected content type: {content_type}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"Request to {url} failed: {e}")
            return None

    def save_to_db(self, df, batch_size=100):
        """ Save the scraped data into the database in batches. """
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT company, title
                        FROM jobs_jobpost
                        WHERE posted_at >= NOW() - INTERVAL '30 days'
                    """)
                    existing_jobs_set = set(cur.fetchall())

                    values = [
                        (
                            row.get('vacancy', '')[:500],
                            '',  # Description left blank for now
                            row.get('company', '')[:500],
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
                        for _, row in df.iterrows()
                        if (row.get('company', ''), row.get('vacancy', '')) not in existing_jobs_set
                    ]

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
            parsers = [
                self.parse_glorri(session),
                self.parse_azercell(session),
                self.parse_azerconnect(session),
                self.parse_djinni_co(session),
                self.parse_abb(session),
                self.parse_hellojob_az(session),
                self.parse_boss_az(session),
                self.parse_ejob_az(session),
                self.parse_vakansiya_az(session),
                self.parse_ishelanlari_az(session),
                self.parse_banker_az(session),
                self.parse_smartjob_az(session),
                self.parse_offer_az(session),
                self.parse_isveren_az(session),
                self.parse_isqur(session),
                self.parse_kapitalbank(session),
                self.parse_bank_of_baku_az(session),
                self.parse_jobbox_az(session),
                self.parse_vakansiya_biz(session),
                self.parse_its_gov(session),
            ]

            all_jobs = await asyncio.gather(*parsers)

            # Flatten and filter results
            all_jobs = [job for job_list in all_jobs if isinstance(job_list, pd.DataFrame) and not job_list.empty for job in job_list.to_dict('records')]

            if all_jobs:
                self.data = pd.DataFrame(all_jobs)
                self.data['scrape_date'] = datetime.now()
                self.data.dropna(subset=['company', 'vacancy'], inplace=True)


    async def parse_glorri(self, session):
        """Fetch all companies and their job data from Glorri."""
        logger.info("Started scraping Glorri")
        url_companies = "https://atsapp.glorri.az/company-service/v2/companies/public"
        limit = 18
        all_jobs = []
        offset = 0

        while True:
            params = {'limit': limit, 'offset': offset}
            companies_data = await self.fetch_url_async(url_companies, session, params=params)
            if not companies_data:
                logger.error("Failed to retrieve companies data.")
                break

            companies = companies_data.get('entities', [])
            if not companies:
                break

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
                        if not jobs_data or not jobs_data.get('entities', []):
                            break

                        for job in jobs_data['entities']:
                            all_jobs.append({
                                'company': company_name,
                                'Company Slug': slug,
                                'vacancy': job['title'],
                                'apply_link': f"https://jobs.glorri.az/vacancies/{slug}/{job['slug']}/apply"
                            })
                        job_offset += limit
            offset += limit

        logger.info("Completed scraping Glorri")
        return all_jobs

    async def parse_azercell(self, session):
        logger.info("Started scraping Azercell")
        url = "https://www.azercell.com/az/about-us/career.html"
        response_text = await self.fetch_url_async(url, session)
        if not response_text:
            logger.warning("Failed to retrieve Azercell page.")
            return pd.DataFrame()

        soup = BeautifulSoup(response_text, "html.parser")
        vacancies_section = soup.find("section", class_="section_vacancies")
        if not vacancies_section:
            logger.warning("Vacancies section not found on Azercell page.")
            return pd.DataFrame()

        job_listings = vacancies_section.find_all("a", class_="vacancies__link")
        tasks = [self.fetch_url_async(urljoin(url, link["href"]), session) for link in job_listings]
        job_pages = await asyncio.gather(*tasks)

        jobs_data = []
        for i, job_page in enumerate(job_pages):
            if job_page:
                job_soup = BeautifulSoup(job_page, "html.parser")
                jobs_data.append({
                    'company': 'azercell',
                    "vacancy": job_listings[i].find("h4", class_="vacancies__name").text,
                    "location": job_listings[i].find("span", class_="vacancies__location").text.strip(),
                    "apply_link": job_listings[i]["href"],
                    "function": job_soup.find("span", class_="function").text if job_soup.find("span", class_="function") else None,
                    "schedule": job_soup.find("span", class_="schedule").text if job_soup.find("span", class_="schedule") else None,
                    "deadline": job_soup.find("span", class_="deadline").text if job_soup.find("span", class_="deadline") else None,
                    "responsibilities": job_soup.find("div", class_="responsibilities").text.strip() if job_soup.find("div", class_="responsibilities") else None,
                    "requirements": job_soup.find("div", class_="requirements").text.strip() if job_soup.find("div", class_="requirements") else None
                })

        logger.info("Completed scraping Azercell")
        return pd.DataFrame(jobs_data)

    async def parse_azerconnect(self, session):
        logger.info("Started scraping Azerconnect")
        url = "https://www.azerconnect.az/vacancies"
        response_text = await self.fetch_url_async(url, session, verify_ssl=False)
        if not response_text:
            logger.warning("Failed to retrieve Azerconnect page.")
            return pd.DataFrame()

        soup = BeautifulSoup(response_text, 'html.parser')
        job_listings = soup.find_all('div', class_='CollapsibleItem_item__CB3bC')

        jobs_data = []
        for job in job_listings:
            content_block = job.find('div', class_='CollapsibleItem_contentInner__vVcvk')
            title = job.find('div', class_='CollapsibleItem_toggle__XNu5y').find('span').text.strip() if job.find('div', class_='CollapsibleItem_toggle__XNu5y').find('span') else "No Title"
            apply_link_elem = job.find('a', class_='Button_button-blue__0wZ4l')
            apply_link = apply_link_elem['href'] if apply_link_elem else "No Apply Link"

            details = content_block.find_all('p')
            function = schedule = deadline = responsibilities = requirements = ""

            for detail in details:
                text = detail.get_text(strip=True)
                if text.startswith("Funksiya:") or text.startswith("İdarə:"):
                    function = text.replace("Funksiya:", "").replace("İdarə:", "").strip()
                elif text.startswith("İş qrafiki:"):
                    schedule = text.replace("İş qrafiki:", "").strip()
                elif text.startswith("Son müraciət tarixi:"):
                    deadline = text.replace("Son müraciət tarixi:", "").strip()
                elif text.startswith("Vəzifənin tələbləri:"):
                    requirements = text.replace("Vəzifənin tələbləri:", "").strip()
                elif text.startswith("Sizin vəzifə öhdəlikləriniz:") or text.startswith("Əlavə Dəyərli Xidmətlər əməliyyatları üzrə ekspert olaraq sizin vəzifə öhdəlikləriniz:"):
                    responsibilities = text.replace("Sizin vəzifə öhdəlikləriniz:", "").strip()

            uls = content_block.find_all('ul')
            if uls:
                for ul in uls:
                    if "Vəzifənin tələbləri" in ul.previous_sibling.get_text(strip=True):
                        requirements += '\n' + '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])
                    elif "Sizin əsas vəzifə öhdəlikləriniz" in ul.previous_sibling.get_text(strip=True):
                        responsibilities += '\n' + '\n'.join([li.get_text(strip=True) for li in ul.find_all('li')])

            if deadline:
                try:
                    deadline_date = datetime.strptime(deadline, "%d.%m.%Y").date() if '.' in deadline else datetime.strptime(deadline, "%d %B %Y").date()
                except ValueError:
                    deadline_date = None
            else:
                deadline_date = None

            jobs_data.append({
                'company': 'azerconnect',
                'vacancy': title,
                'location': 'Baku, Azerbaijan',
                'function': function,
                'schedule': schedule,
                'deadline': deadline_date,
                'responsibilities': responsibilities,
                'requirements': requirements,
                'apply_link': apply_link
            })

        logger.info("Completed scraping Azerconnect")
        return pd.DataFrame(jobs_data)

    async def parse_djinni_co(self, session):
        pages = 17
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
        for page_num in range(1, 7):
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
        logger.info("Scraping completed for busy.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_hellojob_az(self, session):
        logger.info("Started scraping of hellojob.az")
        job_vacancies = []
        base_url = "https://www.hellojob.az"

        for page_number in range(1, 13):
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
        
        for page_num in range(1, 23):  # Scrape from page 1 to 20
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

    async def parse_ejob_az(self, session):
        start_page = 1
        end_page = 20
        logger.info("Scraping started for ejob.az")
        base_url = "https://ejob.az/is-elanlari"
        all_jobs = []
        
        for page in range(start_page, end_page + 1):
            url = f"{base_url}/page-{page}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            response = await self.fetch_url_async(url, session, params=None, verify_ssl=True)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_tables = soup.find_all('table', class_='background')
                for job in job_tables:
                    title_link = job.find('a', href=True)
                    company = job.find('div', class_='company').text if job.find('div', class_='company') else 'No company listed'
                    all_jobs.append({
                        'company': company,
                        'vacancy': title_link.text.strip(),
                        'apply_link': f"https://ejob.az{title_link['href']}"
                    })
            else:
                logger.warning(f"Failed to retrieve page {page}.")

        logger.info("Scraping completed for ejob.az")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_vakansiya_az(self, session):
        logger.info("Scraping started for vakansiya.az")
        url = 'https://www.vakansiya.az/az/'
        response = await self.fetch_url_async(url, session)
        
        if response:
            soup = BeautifulSoup(response, 'html.parser')
            jobs = []
            job_divs = soup.find_all('div', id='js-jobs-wrapper')

            for job_div in job_divs:
                company = job_div.find_all('div', class_='js-fields')[1].find('a')
                title = job_div.find('a', class_='jobtitle')
                apply_link = title['href'] if title else None

                jobs.append({
                    'company': company.get_text(strip=True) if company else 'N/A',
                    'vacancy': title.get_text(strip=True) if title else 'N/A',
                    'apply_link': f'https://www.vakansiya.az{apply_link}' if apply_link else 'N/A'
                })

            logger.info("Scraping completed for vakansiya.az")
            return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to retrieve the page.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_ishelanlari_az(self, session):
        logger.info("Scraping started for ishelanlari.az")
        url = "https://ishelanlari.az/az/vacancies//0/360/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = await self.fetch_url_async(url, session, params=None, verify_ssl=True)

        if response:
            soup = BeautifulSoup(response, 'html.parser')
            vacancies = []
            for job in soup.find_all("div", class_="card-body"):
                title_element = job.find("h2", class_="font-weight-bold")
                company_element = job.find("a", class_="text-muted")
                details_link_element = job.find("a", class_="position-absolute")

                title = title_element.text.strip() if title_element else "No title provided"
                company = company_element.text.strip() if company_element else "No company provided"
                link = details_link_element["href"] if details_link_element else "No link provided"

                vacancies.append({
                    "company": company,
                    "vacancy": title,
                    "apply_link": "https://ishelanlari.az" + link
                })

            logger.info("Scraping completed for ishelanlari.az")
            return pd.DataFrame(vacancies) if vacancies else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to retrieve data for ishelanlari.az.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_banker_az(self, session):
        logger.info("Started scraping Banker.az")
        base_url = 'https://banker.az/vakansiyalar'
        num_pages = 5

        all_job_titles = []
        all_company_names = []
        all_apply_links = []

        for page in range(1, num_pages + 1):
            url = f"{base_url}/page/{page}/"
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_listings = soup.find_all('div', class_='list-data')

                for job in job_listings:
                    job_info = job.find('div', class_='job-info')
                    title_tag = job_info.find('a') if job_info else None
                    title = title_tag.text.strip() if title_tag else None
                    link = title_tag['href'] if title_tag else None

                    company_logo = job.find('div', class_='company-logo')
                    company_img = company_logo.find('img') if company_logo else None
                    company = company_img.get('alt') if company_img else None

                    if title and '-' in title:
                        title_parts = title.split(' – ')
                        title = title_parts[0].strip()
                        if len(title_parts) > 1:
                            company = title_parts[1].strip()

                    if title and company and link:
                        all_job_titles.append(title)
                        all_company_names.append(company)
                        all_apply_links.append(link)
            else:
                logger.warning(f"Failed to retrieve page {page}.")

        df = pd.DataFrame({'company': all_company_names, 'vacancy': all_job_titles, 'apply_link': all_apply_links})
        logger.info("Scraping completed for Banker.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_smartjob_az(self, session):
        logger.info("Started scraping SmartJob.az")
        jobs = []

        for page in range(1, 11):
            url = f"https://smartjob.az/vacancies?page={page}"
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, "html.parser")
                job_listings = soup.find_all('div', class_='item-click')

                if not job_listings:
                    continue

                for listing in job_listings:
                    title = listing.find('div', class_='brows-job-position').h3.a.text.strip()
                    company = listing.find('span', class_='company-title').a.text.strip()
                    jobs.append({
                        'company': company,
                        'vacancy': title,
                        'apply_link': listing.find('div', class_='brows-job-position').h3.a['href']
                    })
            else:
                logger.warning(f"Failed to retrieve page {page}.")

        logger.info("Scraping completed for SmartJob.az")
        return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_offer_az(self, session):
        logger.info("Started scraping offer.az")
        base_url = "https://www.offer.az/is-elanlari/page/"
        all_jobs = []

        for page_number in range(1, 8):
            url = f"{base_url}{page_number}/"
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_cards = soup.find_all('div', class_='job-card')

                for job_card in job_cards:
                    title_tag = job_card.find('a', class_='job-card__title')
                    title = title_tag.text.strip() if title_tag else "N/A"
                    link = title_tag['href'] if title_tag else "N/A"
                    company_tag = job_card.find('p', class_='job-card__meta')
                    company = company_tag.text.strip() if company_tag else "N/A"

                    all_jobs.append({
                        'vacancy': title,
                        'company': company,
                        'location': 'N/A',  # Placeholder, as location is not extracted
                        'apply_link': link,
                        'description': job_card.find('p', class_='job-card__excerpt').text.strip() if job_card.find('p', class_='job-card__excerpt') else "N/A"
                    })
            else:
                logger.warning(f"Failed to retrieve page {page_number}.")

        logger.info("Scraping completed for offer.az")
        return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=['vacancy', 'company', 'location', 'apply_link', 'description'])

    async def parse_isveren_az(self, session):
        start_page = 1
        end_page = 15
        max_retries = 3
        backoff_factor = 1
        jobs = []

        for page_num in range(start_page, end_page + 1):
            retries = 0
            while retries < max_retries:
                try:
                    logger.info(f"Scraping started for isveren.az page {page_num}")
                    url = f"https://isveren.az/?page={page_num}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
                    }

                    response = await self.fetch_url_async(url, session, headers=headers)

                    if response:
                        soup = BeautifulSoup(response, 'html.parser')
                        job_cards = soup.find_all('div', class_='job-card')

                        for job_card in job_cards:
                            title_element = job_card.find('h5', class_='job-title')
                            company_element = job_card.find('p', class_='job-list')
                            link_element = job_card.find('a', href=True)

                            title = title_element.text.strip() if title_element else "No title provided"
                            company = company_element.text.strip() if company_element else "No company provided"
                            link = link_element['href'] if link_element else "No link provided"

                            jobs.append({
                                'company': company,
                                'vacancy': title,
                                'apply_link': link
                            })

                        break  # Exit the retry loop if the request was successful
                    else:
                        logger.error(f"Failed to retrieve page {page_num}.")
                        break

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    retries += 1
                    logger.warning(f"Attempt {retries} for page {page_num} failed: {e}")
                    if retries < max_retries:
                        sleep_time = backoff_factor * (2 ** (retries - 1))
                        logger.info(f"Retrying page {page_num} in {sleep_time} seconds...")
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(f"Max retries exceeded for page {page_num}")

        df = pd.DataFrame(jobs)
        logger.info("Scraping completed for isveren.az")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_isqur(self, session):
        start_page = 1
        end_page = 5
        logger.info("Started scraping isqur.com")
        job_vacancies = []
        base_url = "https://isqur.com/is-elanlari/sehife-"

        for page_num in range(start_page, end_page + 1):
            logger.info(f"Scraping page {page_num} for isqur.com")
            url = f"{base_url}{page_num}"
            response = await self.fetch_url_async(url, session)
            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_cards = soup.find_all('div', class_='kart')
                for job in job_cards:
                    title = job.find('div', class_='basliq').text.strip()
                    company = "Unknown"  # The provided HTML does not include a company name
                    link = "https://isqur.com/" + job.find('a')['href']
                    job_vacancies.append({'company': company, 'vacancy': title, 'apply_link': link})
            else:
                logger.error(f"Failed to retrieve page {page_num} for isqur.com")

        logger.info("Scraping completed for isqur.com")
        return pd.DataFrame(job_vacancies) if job_vacancies else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_kapitalbank(self, session):
        logger.info("Fetching jobs from Kapital Bank API")
        url = "https://apihr.kapitalbank.az/api/Vacancy/vacancies?Skip=0&Take=150&SortField=id&OrderBy=true"
        response = await self.fetch_url_async(url, session)

        if response:
            data = response.get('data', [])
            if not data:
                logger.warning("No job data found in the API response.")
                return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

            jobs_data = []
            for job in data:
                jobs_data.append({
                    'company': 'Kapital Bank',
                    'vacancy': job['header'],
                    'apply_link': f"https://hr.kapitalbank.az/vacancy/{job['id']}"
                })

            logger.info("Job data fetched and parsed successfully from Kapital Bank API")
            return pd.DataFrame(jobs_data)
        else:
            logger.error("Failed to fetch data from Kapital Bank API.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_bank_of_baku_az(self, session):
        logger.info("Scraping started for Bank of Baku")
        url = "https://careers.bankofbaku.com/az/vacancies"
        response = await self.fetch_url_async(url, session, verify_ssl=False)

        if response:
            soup = BeautifulSoup(response, 'html.parser')
            jobs = []
            job_blocks = soup.find_all('div', class_='main-cell mc-50p')

            for job_block in job_blocks:
                link_tag = job_block.find('a')
                if link_tag:
                    link = 'https://careers.bankofbaku.com' + link_tag['href']
                    job_info = job_block.find('div', class_='vacancy-list-block-content')
                    title = job_info.find('div', class_='vacancy-list-block-header').get_text(
                        strip=True) if job_info else 'No title provided'
                    department_label = job_info.find('label', class_='light-red-bg')
                    deadline = department_label.get_text(strip=True) if department_label else 'No deadline listed'
                    department_info = job_info.find_all('label')[0].get_text(strip=True) if len(
                        job_info.find_all('label')) > 0 else 'No department listed'
                    location_info = job_info.find_all('label')[1].get_text(strip=True) if len(
                        job_info.find_all('label')) > 1 else 'No location listed'

                    jobs.append({'company': 'Bank of Baku', 'vacancy': title, 'apply_link': link})

            logger.info("Scraping completed for Bank of Baku")
            return pd.DataFrame(jobs) if jobs else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])
        else:
            logger.error("Failed to retrieve data for Bank of Baku.")
            return pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_jobbox_az(self, session):
        start_page=1
        end_page=10
        logger.info(f"Scraping started for jobbox.az from page {start_page} to page {end_page}")
        start_page=1
        end_page=5
        job_vacancies = []
        for page_num in range(start_page, end_page + 1):
            logger.info(f"Scraping page {page_num}")
            url = f'https://jobbox.az/az/vacancies?page={page_num}'
            response = await self.fetch_url_async(url, session)

            if response:
                soup = BeautifulSoup(response, 'html.parser')
                job_items = soup.find_all('li', class_='item')

                for item in job_items:
                    job = {}

                    link_tag = item.find('a')
                    if link_tag:
                        job['apply_link'] = link_tag['href']
                    else:
                        continue  # Skip if no link found

                    title_ul = item.find('ul', class_='title')
                    if title_ul:
                        title_div = title_ul.find_all('li')
                        job['vacancy'] = title_div[0].text.strip() if len(title_div) > 0 else None
                    else:
                        continue  # Skip if title information is missing

                    address_ul = item.find('ul', class_='address')
                    if address_ul:
                        address_div = address_ul.find_all('li')
                        job['company'] = address_div[0].text.strip() if len(address_div) > 0 else None
                    else:
                        continue  # Skip if address information is missing

                    job_vacancies.append(job)
            else:
                logger.error(f"Failed to retrieve page {page_num}.")

        df = pd.DataFrame(job_vacancies, columns=['company', 'vacancy', 'apply_link'])
        logger.info("Scraping completed for jobbox.az")
        logger.info(df)
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_vakansiya_biz(self, session):
        logger.info("Started scraping Vakansiya.biz")
        base_url = "https://api.vakansiya.biz/api/v1/vacancies/search"
        headers = {'Content-Type': 'application/json'}
        page = 1
        all_jobs = []

        while True:
            response = await self.fetch_url_async(
                f"{base_url}?page={page}&country_id=108&city_id=0&industry_id=0&job_type_id=0&work_type_id=0&gender=-1&education_id=0&experience_id=0&min_salary=0&max_salary=0&title=",
                session,
                headers=headers
            )

            if not response:
                logger.error(f"Failed to fetch page {page}")
                break

            data = response.get('data', [])
            all_jobs.extend(data)

            if not response.get('next_page_url'):
                break

            page += 1

        job_listings = [{
            'company': job['company_name'].strip().lower(),
            'vacancy': job['title'].strip().lower(),
            'apply_link': f"https://vakansiya.biz/az/vakansiyalar/{job['id']}/{job['slug']}"
        } for job in all_jobs]

        df = pd.DataFrame(job_listings)
        logger.info("Scraping completed for Vakansiya.biz")
        return df if not df.empty else pd.DataFrame(columns=['company', 'vacancy', 'apply_link'])

    async def parse_its_gov(self, session):
        start_page = 1
        end_page = 20
        logger.info(f"Scraping its.gov.az from page {start_page} to page {end_page}")
        base_url = "https://its.gov.az/page/vakansiyalar?page="
        all_vacancies = []

        for page in range(start_page, end_page + 1):
            url = f"{base_url}{page}"
            logger.info(f"Fetching page {page}")
            response = await self.fetch_url_async(url, session)
            
            if response:
                soup = BeautifulSoup(response, "html.parser")
                events = soup.find_all('div', class_='event')
                if not events:
                    logger.info(f"No job listings found on page {page}")
                    break

                for event in events:
                    title_tag = event.find('a', class_='event__link')
                    if title_tag:
                        title = title_tag.get_text(strip=True).lower()
                        link = title_tag['href']
                        deadline_tag = event.find('span', class_='event__time')
                        deadline = deadline_tag.get_text(strip=True) if deadline_tag else 'N/A'
                        all_vacancies.append({
                            'company': 'icbari tibbi sigorta',  # Normalized company name
                            'vacancy': title,
                            'apply_link': link
                        })
            else:
                logger.warning(f"Failed to retrieve page {page}")

        df = pd.DataFrame(all_vacancies)
        logger.info("Scraping completed for its.gov.az")
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
