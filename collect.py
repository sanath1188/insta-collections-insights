import csv
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
collection_id = os.getenv("COLLECTION_ID")

def fetch_collection_posts(collection_id, cookies_header, csv_filename):
    base_url = f"https://www.instagram.com/api/v1/feed/collection/{collection_id}/posts/"
    max_id = ""
    session = requests.Session()

    # Prepare headers from your curl request
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        # Ensure 'yourusername' and 'yourcollectionname' in referer are updated if necessary
        "referer": f"https://www.instagram.com/yourusername/saved/yourcollectionname/{collection_id}/",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-full-version-list": '"Chromium";v="136.0.7103.113", "Google Chrome";v="136.0.7103.113", "Not.A/Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"macOS"',
        "sec-ch-ua-platform-version": '"15.4.1"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-asbd-id": "359341",
        "x-csrftoken": "",  # will be filled below from cookies
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "",  # optional
        "x-requested-with": "XMLHttpRequest",
        "x-web-session-id": "",  # optional
    }

    # Extract csrftoken from cookies_header string
    def extract_cookie_value(cookie_str, key):
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith(key + "="):
                return part[len(key)+1:]
        return ""

    csrftoken = extract_cookie_value(cookies_header, "csrftoken")
    if not csrftoken:
        print("Warning: csrftoken not found in cookies. This might lead to issues.")
    headers["x-csrftoken"] = csrftoken

    # Add cookies to session
    cookies = {}
    for cookie_part in cookies_header.split(";"):
        if "=" in cookie_part:
            k, v = cookie_part.strip().split("=", 1)
            cookies[k] = v
    session.cookies.update(cookies)

    # Open CSV file for writing
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Reel URL', 'Caption']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        while True:
            print("max_id", {max_id})
            params = {"max_id": max_id} if max_id else {}
            try:
                response = session.get(base_url, headers=headers, params=params)
                response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch data: {e}")
                break
            
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                print(f"Failed to decode JSON response. Status code: {response.status_code}, Response text: {response.text[:200]}")
                break


            items = data.get("items", [])
            if not items and not data.get("more_available", False): # Check if items list is empty and no more available
                if max_id == "": # If this is the first request and no items
                     print("No items found in the collection or collection is private/invalid.")
                else: # No more items on subsequent pages
                     print("No more items found.")
                break


            for item in items:
                media = item.get("media", {})
                code = media.get("code")
                caption_obj = media.get("caption", {})
                caption_text = caption_obj.get("text", "") if caption_obj else "" # Handle cases where caption object is None
                reel_url = f"https://www.instagram.com/reel/{code}/" if code else "Unknown URL"
                
                print(f"Reel URL: {reel_url}")
                # print(f"Caption: {caption_text}")
                # print("-" * 40)

                # Write to CSV
                writer.writerow({'Reel URL': reel_url, 'Caption': caption_text})

            if not data.get("more_available", False):
                break

            max_id = data.get("next_max_id", "")
            if not max_id:
                break
    print(f"Data fetching complete. Output saved to {csv_filename}")


if __name__ == "__main__":
    # IG_COOKIES will be loaded from .env file or system environment variables
    cookies_header = os.getenv("IG_COOKIES")
    if not cookies_header:
        print("Error: IG_COOKIES environment variable not found.")
        print("Please ensure it is set in your system environment or in a .env file in the script's directory.")
        print("Example .env file content: IG_COOKIES=\"your_full_cookie_string_here\"")
        exit(1)

    # Replace with your actual collection ID
    collection_id = collection_id # Example, replace with your target collection ID
    csv_filename = "instagram_collection_posts.csv" # Name of the output CSV file

    print(f"Fetching posts for collection ID: {collection_id}")
    fetch_collection_posts(collection_id, cookies_header, csv_filename)
