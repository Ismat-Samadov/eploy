#!/usr/bin/env python3
"""
MedPortal.az Doctor Listings Scraper
Scrapes doctor listings and contact information from medportal.az
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
import pandas as pd
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

class MedPortalScraper:
    def __init__(self, max_pages: Optional[int] = None):
        self.base_url = "https://medportal.az"
        self.search_url = f"{self.base_url}/search"
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.doctors_data = []

    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'lxml')
            except requests.RequestException as e:
                print(f"Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
        return None

    def extract_doctor_listings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract doctor listings from search results page"""
        listings = []
        doctor_boxes = soup.find_all('div', class_='doctor-box')

        for box in doctor_boxes:
            try:
                # Extract detail link (haqqimizda page)
                detail_link_tag = box.find('div', class_='detail-box-doctor').find('a')
                if not detail_link_tag:
                    continue

                detail_url = detail_link_tag.get('href', '')
                if not detail_url:
                    continue

                # Make absolute URL
                if not detail_url.startswith('http'):
                    detail_url = urljoin(self.base_url, detail_url)

                # Extract name
                name_tag = box.find('div', class_='detail-box-doctor').find('h4')
                name = name_tag.text.strip() if name_tag else 'N/A'

                # Extract specialty
                specialty_tag = box.find('div', class_='detail-box-doctor').find('p')
                specialty = specialty_tag.text.strip() if specialty_tag else 'N/A'

                # Extract image
                img_tag = box.find('div', class_='img-box-doctor').find('img')
                image_url = img_tag.get('src', '') if img_tag else ''
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)

                listings.append({
                    'name': name,
                    'specialty': specialty,
                    'detail_url': detail_url,
                    'image_url': image_url
                })
            except Exception as e:
                print(f"Error extracting listing: {e}")
                continue

        return listings

    def modify_url_to_contact_page(self, url: str) -> str:
        """Modify URL to show contact page (sehife=elaqe)"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params['sehife'] = ['elaqe']
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract contact information from contact page"""
        contact_info = {
            'phones': [],
            'location': '',
            'working_hours': '',
            'clinic_name': ''
        }

        try:
            # Find contact section
            contact_back = soup.find('div', class_='contact-back')
            if not contact_back:
                return contact_info

            # Extract phone numbers
            phone_section = contact_back.find('div', class_='item-contact')
            if phone_section:
                phone_links = phone_section.find_all('a', href=re.compile(r'tel:'))
                for link in phone_links:
                    phone = link.text.strip()
                    if phone and phone not in contact_info['phones']:
                        contact_info['phones'].append(phone)

            # Extract location and clinic info
            location_sections = contact_back.find_all('div', class_='item-contact')
            for section in location_sections:
                # Look for location marker icon
                if section.find('i', class_='fa-map-marker-alt'):
                    paragraphs = section.find_all('p')
                    if len(paragraphs) >= 1:
                        contact_info['clinic_name'] = paragraphs[0].text.strip()
                    if len(paragraphs) >= 2:
                        contact_info['working_hours'] = paragraphs[1].text.strip()

        except Exception as e:
            print(f"Error extracting contact info: {e}")

        return contact_info

    def get_total_pages(self) -> int:
        """Get total number of pages from pagination"""
        soup = self.get_page(f"{self.search_url}?page=1")
        if not soup:
            return 1

        pagination = soup.find('ul', class_='doctor-pagination')
        if not pagination:
            return 1

        page_links = pagination.find_all('li')
        max_page = 1

        for li in page_links:
            link = li.find('a')
            if link:
                page_num_match = re.search(r'page=(\d+)', link.get('href', ''))
                if page_num_match:
                    page_num = int(page_num_match.group(1))
                    max_page = max(max_page, page_num)

        return max_page

    def scrape_all_pages(self):
        """Main scraping function to scrape all pages"""
        print("Starting MedPortal.az scraper...")

        # Get total pages
        total_pages = self.get_total_pages()
        print(f"Total pages found: {total_pages}")

        # Limit pages if max_pages is set
        if self.max_pages:
            total_pages = min(total_pages, self.max_pages)
            print(f"Limiting to {total_pages} pages")

        # Iterate through all pages
        for page_num in range(1, total_pages + 1):
            print(f"\n{'='*60}")
            print(f"Scraping page {page_num}/{total_pages}")
            print(f"{'='*60}")

            page_url = f"{self.search_url}?page={page_num}"
            soup = self.get_page(page_url)

            if not soup:
                print(f"Failed to fetch page {page_num}, skipping...")
                continue

            # Extract listings from this page
            listings = self.extract_doctor_listings(soup)
            print(f"Found {len(listings)} listings on page {page_num}")

            # For each listing, get contact information
            for idx, listing in enumerate(listings, 1):
                print(f"\n[{idx}/{len(listings)}] Processing: {listing['name']}")

                # Modify URL to contact page
                contact_url = self.modify_url_to_contact_page(listing['detail_url'])
                print(f"  Fetching contact info from: {contact_url}")

                # Get contact page
                contact_soup = self.get_page(contact_url)

                if contact_soup:
                    contact_info = self.extract_contact_info(contact_soup)

                    # Create base data
                    base_data = {
                        **listing,
                        'clinic_name': contact_info['clinic_name'],
                        'working_hours': contact_info['working_hours'],
                        'contact_url': contact_url
                    }

                    # Create separate row for each phone number
                    phones = contact_info['phones'] if contact_info['phones'] else ['N/A']
                    for phone in phones:
                        doctor_data = {
                            **base_data,
                            'phone': phone
                        }
                        self.doctors_data.append(doctor_data)

                    print(f"  ✓ Extracted: {len(contact_info['phones'])} phone(s)")
                else:
                    print(f"  ✗ Failed to fetch contact page")

                # Be respectful to the server
                time.sleep(1)

            # Pause between pages
            if page_num < total_pages:
                print(f"\nPausing before next page...")
                time.sleep(2)

        print(f"\n{'='*60}")
        print(f"Scraping completed! Total records: {len(self.doctors_data)}")
        print(f"{'='*60}")

    def save_to_json(self, filename: str = 'doctors_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.doctors_data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")

    def save_to_csv(self, filename: str = 'doctors_data.csv'):
        """Save scraped data to CSV file"""
        if not self.doctors_data:
            print("No data to save")
            return

        # Define column order
        fieldnames = ['name', 'specialty', 'phone', 'clinic_name', 'working_hours',
                      'detail_url', 'image_url', 'contact_url']

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.doctors_data)
        print(f"Data saved to {filename}")

    def save_to_xlsx(self, filename: str = 'doctors_data.xlsx'):
        """Save scraped data to XLSX file"""
        if not self.doctors_data:
            print("No data to save")
            return

        # Create DataFrame with ordered columns
        df = pd.DataFrame(self.doctors_data)
        column_order = ['name', 'specialty', 'phone', 'clinic_name', 'working_hours',
                        'detail_url', 'image_url', 'contact_url']

        # Reorder columns
        df = df[[col for col in column_order if col in df.columns]]

        # Save to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Data saved to {filename}")


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        MedPortal.az Doctor Listings Scraper              ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Create scraper instance
    # Set max_pages=None to scrape all pages, or set a number to limit
    scraper = MedPortalScraper(max_pages=None)  # Change to specific number for testing

    # Run the scraper
    scraper.scrape_all_pages()

    # Save results in all formats
    print("\nSaving data...")
    scraper.save_to_csv('doctors_data.csv')
    scraper.save_to_xlsx('doctors_data.xlsx')
    scraper.save_to_json('doctors_data.json')

    print("\n✓ All done!")


if __name__ == "__main__":
    main()
