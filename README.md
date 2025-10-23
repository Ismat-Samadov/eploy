# MedPortal.az Doctor Listings Scraper

A Python web scraper that extracts doctor and clinic listings along with their contact information from medportal.az.

## Features

- Scrapes all pages from medportal.az search results
- Extracts doctor/clinic information including:
  - Name
  - Specialty
  - Phone numbers
  - Clinic name
  - Working hours
  - Profile image URL
  - Detail page URL
- Exports data to both JSON and CSV formats
- Includes retry logic and rate limiting to be respectful to the server
- Progress tracking during scraping

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Scrape All Pages)

```bash
python medportal_scraper.py
```

This will scrape all pages and save results to:
- `doctors_data.json` - JSON format
- `doctors_data.csv` - CSV format

### Test with Limited Pages

To test the scraper with only a few pages, edit `medportal_scraper.py` and change:

```python
scraper = MedPortalScraper(max_pages=None)  # Scrape all pages
```

to:

```python
scraper = MedPortalScraper(max_pages=3)  # Scrape only first 3 pages
```

## Output Format

### CSV Format
The CSV file will contain the following columns:
- `name` - Doctor/clinic name
- `specialty` - Medical specialty
- `detail_url` - Link to detail page
- `image_url` - Profile image URL
- `phones` - Phone numbers (comma-separated)
- `clinic_name` - Clinic/location name
- `working_hours` - Working hours/schedule
- `contact_url` - Direct link to contact page

### JSON Format
The JSON file contains an array of objects with the same fields.

## How It Works

1. **Fetch Search Pages**: The scraper starts by fetching all search result pages from `https://medportal.az/search?page=X`

2. **Extract Listings**: From each search page, it extracts doctor/clinic listings from the HTML structure

3. **Fetch Contact Info**: For each listing, it:
   - Takes the detail page URL
   - Modifies the URL parameter to `sehife=elaqe` to access the contact page
   - Extracts phone numbers and other contact information

4. **Save Data**: Finally, it saves all collected data to JSON and CSV files

## Rate Limiting

The scraper includes rate limiting to be respectful to the server:
- 1 second delay between individual doctor pages
- 2 seconds delay between search result pages

## Error Handling

- Automatic retry with exponential backoff for failed requests
- Graceful handling of missing data
- Continue scraping even if individual pages fail

## Notes

- The scraper respects robots.txt conventions
- Please use responsibly and don't overload the server
- Consider running during off-peak hours for large scraping jobs
- The website structure may change over time, requiring updates to the scraper

## Example Output

```json
[
  {
    "name": "Xanoğlan Qənbərov",
    "specialty": "Nevroloq",
    "detail_url": "https://medportal.az/menu/hekimler/nevroloq/xanoglan-qenberov-1731590329?sehife=haqqimizda",
    "image_url": "https://medportal.az/storage/files/1/images/user-profil/914-e7ff86ab-4669-4d35-a3d1-aa43483e6c81.jpg",
    "phones": "(050) 322 94 11",
    "clinic_name": "Leyla Medical Center",
    "working_hours": "Bazar Ertəsi - Cümə",
    "contact_url": "https://medportal.az/menu/hekimler/nevroloq/xanoglan-qenberov-1731590329?sehife=elaqe"
  }
]
```

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Scraper is too slow
**Solution**: You can reduce the sleep times in the code, but be respectful to the server

### Issue: Getting blocked or rate limited
**Solution**: Increase the sleep times between requests or run the scraper during off-peak hours
