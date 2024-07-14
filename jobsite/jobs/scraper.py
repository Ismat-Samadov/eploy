import requests
import brotli

# Define the URL for the API endpoint
url = "https://www.jobsearch.az/api-az/banners"

# Define the headers for the request
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

try:
    # Make the GET request to the API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Handle possible Brotli encoding
        if response.headers.get('Content-Encoding') == 'br':
            decompressed_data = brotli.decompress(response.content)
            raw_text = decompressed_data.decode('utf-8')
        else:
            raw_text = response.text

        # Print the raw response text for debugging
        print("Raw response text:")
        print(raw_text)

        try:
            # Parse the JSON response
            data = response.json()

            # Process the main banner
            main_banner = data.get('main', {})
            print("\nMain Banner:")
            print(main_banner)

            # Process the banners
            banners = data.get('banners', [])
            print("\nBanners:")
            for banner in banners:
                print(banner)

            # Process the statistics
            statistics = data.get('statistics', {})
            print("\nStatistics:")
            print(statistics)

        except requests.exceptions.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
except requests.exceptions.RequestException as req_err:
    print(f"Request error: {req_err}")
