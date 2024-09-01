# import requests

# # Base URL for the API request
# base_url = "https://www.jobsearch.az/api-az/vacancies-az"
# params = {
#     'hl': 'az',
#     'q': '',
#     'posted_date': '',
#     'seniority': '',
#     'categories': '',
#     'industries': '',
#     'ads': '',
#     'location': '',
#     'job_type': '',
#     'salary': '',
#     'order_by': ''
# }

# # Headers for the request
# headers = {
#     'authority': 'www.jobsearch.az',
#     'accept': 'application/json, text/plain, */*',
#     'accept-encoding': 'gzip, deflate, br, zstd',
#     'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
#     'cookie': 'user=%7B%22error%22%3Afalse%2C%22favorites_count%22%3A0%7D; _gcl_au=1.1.1404763121.1725185599; _ga=GA1.2.1933170633.1725185600; _gid=GA1.2.480292949.1725185600; dark_mode=true; _ga_87BPSWHSPN=GS1.2.1725185600.1.1.1725185628.0.0.0; JOB_SEARCH=eyJpdiI6ImhkeElObGhhVDJFR0dWSFNFQVZVakE9PSIsInZhbHVlIjoiTkFsOWlYc0o0SUQwQVlmMHdEUkcvT3BDNTVGQmpmaW9kZFBTS0NVMmF2dms3U2xma3NVS1V6YW1ldWdUVmIyVy8vWGdqVXBzZGZObjZJVVJxbVNrK0Y1L2NaVHo0enNRaktXNmNCZzFKaHozM2d5WDQ3dnN2cHh0MmQ1NHJuMnIiLCJtYWMiOiI4ZTZjMDNkNGE5MGIyZDI5OGY2YWYxNTBhZjVhMzg4OWRjZmY5NGYxYTFiNzllMzM0MmE1NDlhZjJiNTcxYjE5IiwidGFnIjoiIn0%3D',
#     'dnt': '1',
#     'priority': 'u=1, i',
#     'referer': 'https://www.jobsearch.az/vacancies',
#     'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"macOS"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-origin',
#     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
#     'x-requested-with': 'XMLHttpRequest'
# }

# # Function to process each page of results
# def process_jobs(data):
#     for job in data.get('items', []):
#         print(f"ID: {job['id']}")
#         print(f"Title: {job['title']}")
#         print(f"Is New: {job['is_new']}")
#         print(f"Is Favorite: {job['is_favorite']}")
#         print(f"Is VIP: {job['is_vip']}")
#         print(f"Created At: {job['created_at']}")
#         print(f"Slug: {job['slug']}")
#         print(f"Request Type: {job['request_type']}")
#         print(f"Company ID: {job['company']['id']}")
#         print(f"Company Title: {job['company']['title']}")
#         print(f"Company Slug: {job['company']['slug']}")
#         print(f"Company Logo Mini: {job['company']['logo_mini']}")
#         print(f"Company Address: {job['company']['address']}")
#         print(f"Company Phones: {', '.join(job['company']['phones'])}")
#         print(f"Company Website: {job['company']['sites'][0]['url'] if job['company']['sites'] else 'N/A'}")
#         print(f"Company Coordinates: Lat {job['company']['coordinates']['lat']}, Lng {job['company']['coordinates']['lng']}")
#         print(f"Category ID: {job['category']['id']}")
#         print(f"Category Title: {job['category']['title']}")
#         print(f"Category Image Mini: {job['category']['image_mini']}")
#         print(f"Deadline At: {job['deadline_at']}")
#         print(f"Salary: {job['salary']}")
#         print(f"Phone: {job['phone']}")
#         print(f"Hide Company: {job['hide_company']}")
#         print(f"Has Company Info: {job['has_company_info']}")
#         print(f"View Count: {job['view_count']}")
#         print(f"V Count: {job['v_count']}")
#         # Construct the apply link using the slug
#         apply_link = f"https://www.jobsearch.az/vacancies/{job['slug']}"
#         print(f"Apply Link: {apply_link}")
#         print("-" * 40)

# # Initialize page counter
# page_count = 0

# # Loop to fetch and process up to 5 pages
# while page_count < 5:
#     response = requests.get(base_url, params=params, headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         process_jobs(data)
        
#         # Check if there is a next page URL
#         if 'next' in data:
#             next_page_url = data['next']
#             base_url = next_page_url
#             params = {}  # Reset params since the next page URL includes all parameters
#             page_count += 1  # Increment page counter
#         else:
#             break  # No more pages, exit the loop
#     else:
#         print(f"Failed to retrieve data: {response.status_code}")
#         break


import requests
import pandas as pd

def jobsearch_az():
    # Base URL for the API request
    base_url = "https://www.jobsearch.az/api-az/vacancies-az"
    params = {
        'hl': 'az',
        'q': '',
        'posted_date': '',
        'seniority': '',
        'categories': '',
        'industries': '',
        'ads': '',
        'location': '',
        'job_type': '',
        'salary': '',
        'order_by': ''
    }

    # Headers for the request
    headers = {
        'authority': 'www.jobsearch.az',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
        'cookie': 'user=%7B%22error%22%3Afalse%2C%22favorites_count%22%3A0%7D; _gcl_au=1.1.1404763121.1725185599; _ga=GA1.2.1933170633.1725185600; _gid=GA1.2.480292949.1725185600; dark_mode=true; _ga_87BPSWHSPN=GS1.2.1725185600.1.1.1725185628.0.0.0; JOB_SEARCH=eyJpdiI6ImhkeElObGhhVDJFR0dWSFNFQVZVakE9PSIsInZhbHVlIjoiTkFsOWlYc0o0SUQwQVlmMHdEUkcvT3BDNTVGQmpmaW9kZFBTS0NVMmF2dms3U2xma3NVS1V6YW1ldWdUVmIyVy8vWGdqVXBzZGZObjZJVVJxbVNrK0Y1L2NaVHo0enNRaktXNmNCZzFKaHozM2d5WDQ3dnN2cHh0MmQ1NHJuMnIiLCJtYWMiOiI4ZTZjMDNkNGE5MGIyZDI5OGY2YWYxNTBhZjVhMzg4OWRjZmY5NGYxYTFiNzllMzM0MmE1NDlhZjJiNTcxYjE5IiwidGFnIjoiIn0%3D',
        'dnt': '1',
        'priority': 'u=1, i',
        'referer': 'https://www.jobsearch.az/vacancies',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    # List to hold job data
    jobs_list = []

    # Initialize page counter
    page_count = 0

    # Loop to fetch and process up to 5 pages
    while page_count < 5:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()

            # Process each job in the current page
            for job in data.get('items', []):
                job_data = {
                    "ID": job['id'],
                    "Title": job['title'],
                    "Is New": job['is_new'],
                    "Is Favorite": job['is_favorite'],
                    "Is VIP": job['is_vip'],
                    "Created At": job['created_at'],
                    "Slug": job['slug'],
                    "Request Type": job['request_type'],
                    "Company ID": job['company']['id'],
                    "Company Title": job['company']['title'],
                    "Company Slug": job['company']['slug'],
                    "Company Logo Mini": job['company']['logo_mini'],
                    "Company Address": job['company']['address'],
                    "Company Phones": ', '.join(job['company']['phones']),
                    "Company Website": job['company']['sites'][0]['url'] if job['company']['sites'] else 'N/A',
                    "Company Coordinates": f"Lat {job['company']['coordinates']['lat']}, Lng {job['company']['coordinates']['lng']}",
                    "Category ID": job['category']['id'],
                    "Category Title": job['category']['title'],
                    "Category Image Mini": job['category']['image_mini'],
                    "Deadline At": job['deadline_at'],
                    "Salary": job['salary'],
                    "Phone": job['phone'],
                    "Hide Company": job['hide_company'],
                    "Has Company Info": job['has_company_info'],
                    "View Count": job['view_count'],
                    "V Count": job['v_count'],
                    "Apply Link": f"https://www.jobsearch.az/{job['slug']}"
                }
                jobs_list.append(job_data)

            # Check if there is a next page URL
            if 'next' in data:
                next_page_url = data['next']
                base_url = next_page_url
                params = {}  # Reset params since the next page URL includes all parameters
                page_count += 1  # Increment page counter
            else:
                break  # No more pages, exit the loop
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            break

    # Convert the list of jobs to a DataFrame
    df = pd.DataFrame(jobs_list)
    return df


df = jobsearch_az()
print(df.head())  # Display the first few rows of the DataFrame
