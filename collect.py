import csv
import os
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration from Environment Variables ---
IG_COOKIES = os.getenv("IG_COOKIES")
COLLECTION_ID = os.getenv("COLLECTION_ID")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("COLLECTION_ID:", os.getenv("COLLECTION_ID"))
print("COLLECTION_NAME:", os.getenv("COLLECTION_NAME"))

# --- Gemini API Configuration ---
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
GEMINI_MODEL_NAME = "gemini-1.5-pro-latest"

def get_location_from_gemini(caption_text: str, api_key: str) -> dict:
    default_location = {"place_name": None, "city": None, "state": None, "country": None}
    if not caption_text or not caption_text.strip():
        print("Skipping Gemini: Caption is empty or whitespace.")
        return default_location
    
    if not api_key:
        print("Skipping Gemini: API key not provided.")
        return default_location

    gemini_api_url = GEMINI_API_URL_TEMPLATE.format(model_name=GEMINI_MODEL_NAME, api_key=api_key)

    system_instruction_text = (
        "From the provided text, extract the specific name of the place (e.g., restaurant name, park name, landmark name), "
        "the city, the state or region, and the country. "
        "If any piece of information is not present or cannot be clearly identified, try to infer missing information smartly from the context. "
        "For example, if the state is not explicitly mentioned but the city is, infer the state and country from the city. "
        "Similarly, if Jayanagar is mentioned, recognize it as an area within Bangalore city, Karnataka state, India. "
        "Focus on explicit mentions of locations and reasonable inferences. "
        "Return null for any field that cannot be determined or confidently inferred."
    )
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "place_name": {"type": "STRING", "nullable": True, "description": "The specific name of the location/venue mentioned."},
            "city": {"type": "STRING", "nullable": True, "description": "The city where the place is located."},
            "state": {"type": "STRING", "nullable": True, "description": "The state, province, or region where the city is located."},
            "country": {"type": "STRING", "nullable": True, "description": "The country where the place is located."}
        }
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ]

    request_body = {
        "contents": [{"role": "user", "parts": [{"text": caption_text}]}],
        "systemInstruction": {"role": "system", "parts": [{"text": system_instruction_text}]},
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 512,
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        },
        "safetySettings": safety_settings
    }

    try:
        print(f"Sending request to Gemini for caption: '{caption_text[:70]}...'")
        response = requests.post(gemini_api_url, json=request_body, timeout=45)
        
        if response.status_code != 200:
            print(f"Gemini API Error: Status Code {response.status_code}")
            try:
                error_details = response.json()
                print(f"Gemini API Error Body: {error_details}")
            except json.JSONDecodeError:
                print(f"Gemini API Error Body (text): {response.text}")
            response.raise_for_status()

        response_data = response.json()
        
        candidates = response_data.get("candidates", [])
        if candidates:
            content_parts = candidates[0].get("content", {}).get("parts", [])
            if content_parts:
                extracted_text = content_parts[0].get("text")
                if extracted_text:
                    location_data = json.loads(extracted_text) 
                    print(f"Gemini extracted: {location_data}")
                    return {
                        "place_name": location_data.get("place_name"),
                        "city": location_data.get("city"),
                        "state": location_data.get("state"),
                        "country": location_data.get("country") 
                    }
        print(f"Warning: Could not parse location from Gemini response. Response: {response_data}")
        return default_location

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}") 
        return default_location
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e: 
        print(f"Error parsing Gemini response or extracted text: {e}. Extracted text was: '{extracted_text if 'extracted_text' in locals() else 'N/A'}' Response text: {response.text if 'response' in locals() and hasattr(response, 'text') else 'N/A'}")
        return default_location

# MODIFICATION: Logic to read existing URLs and append/skip
def fetch_collection_posts(collection_id, cookies_header, gemini_key, csv_filename):
    if not collection_id:
        print("Error: COLLECTION_ID is not set.")
        return None # Return None if setup fails

    base_url = f"https://www.instagram.com/api/v1/feed/collection/{collection_id}/posts/"
    max_id = ""
    session = requests.Session()
    fieldnames = ['Reel URL', 'Caption', 'Place Name', 'City', 'State', 'Country']
    existing_reel_urls = set()
    new_items_fetched_this_run = 0

    # MODIFICATION: Read existing Reel URLs if CSV exists
    try:
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as f_read:
            reader = csv.DictReader(f_read)
            if 'Reel URL' in reader.fieldnames: # Check if 'Reel URL' column exists
                for row in reader:
                    existing_reel_urls.add(row['Reel URL'])
            else: # Handle case where file exists but doesn't have the expected header (e.g., empty or corrupted)
                print(f"Warning: CSV file '{csv_filename}' exists but does not contain 'Reel URL' header. Treating as empty for appending.")
        print(f"Found {len(existing_reel_urls)} existing reel URLs in '{csv_filename}'.")
    except FileNotFoundError:
        print(f"CSV file '{csv_filename}' not found. A new file will be created.")
    except Exception as e:
        print(f"Error reading existing CSV '{csv_filename}': {e}. Proceeding as if it's a new file.")
        existing_reel_urls.clear() # Ensure it's empty if read fails


    headers = {
        "accept": "*/*", "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "referer": f"https://www.instagram.com/yourusername/saved/yourcollectionname/{collection_id}/", 
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-full-version-list": '"Chromium";v="136.0.7103.113", "Google Chrome";v="136.0.7103.113", "Not.A/Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0", "sec-ch-ua-model": '""', "sec-ch-ua-platform": '"macOS"',
        "sec-ch-ua-platform-version": '"15.4.1"', "sec-fetch-dest": "empty", "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-asbd-id": "359341", "x-csrftoken": "", "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "", "x-requested-with": "XMLHttpRequest", "x-web-session-id": "",
    }

    def extract_cookie_value(cookie_str, key):
        if not cookie_str: return ""
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith(key + "="):
                return part[len(key)+1:]
        return ""

    csrftoken = extract_cookie_value(cookies_header, "csrftoken")
    if not csrftoken: print("Warning: csrftoken not found in cookies.")
    headers["x-csrftoken"] = csrftoken

    insta_cookies = {}
    if cookies_header:
        for cookie_part in cookies_header.split(";"):
            if "=" in cookie_part: k, v = cookie_part.strip().split("=", 1); insta_cookies[k] = v
    session.cookies.update(insta_cookies)

    # MODIFICATION: Open CSV in append mode 'a+', write header only if new
    try:
        with open(csv_filename, mode='a+', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csvfile.seek(0, os.SEEK_END) # Go to the end of the file
            if csvfile.tell() == 0: # Check if file is empty (newly created or truncated)
                writer.writeheader()
                print("Wrote header to new CSV file.")

            page_count = 0
            total_items_processed_from_api = 0 # Count items received from API this run
            
            while True:
                page_count += 1
                print(f"Fetching page {page_count} from Instagram with max_id: '{max_id}'")
                params = {"max_id": max_id} if max_id else {}
                try:
                    response = session.get(base_url, headers=headers, params=params, timeout=20)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch Instagram data: {e}")
                    break
                
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    print(f"Failed to decode Instagram JSON response. Status: {response.status_code}, Text: {response.text[:200]}")
                    break

                items = data.get("items", [])
                if not items and not data.get("more_available", False):
                    if max_id == "": print("No items found in the Instagram collection or collection is private/invalid.")
                    else: print("No more items to fetch from Instagram.")
                    break

                for item_data in items:
                    total_items_processed_from_api += 1
                    media = item_data.get("media", {})
                    code = media.get("code")
                    caption_obj = media.get("caption", {})
                    caption_text = caption_obj.get("text", "") if caption_obj else ""
                    reel_url = f"https://www.instagram.com/reel/{code}/" if code else "Unknown URL"
                    
                    print(f"\nProcessing Instagram item {total_items_processed_from_api}: {reel_url}")

                    # MODIFICATION: Skip if reel_url already exists
                    if reel_url in existing_reel_urls:
                        print(f"Skipping (already exists in CSV): {reel_url}")
                        continue 

                    location_info = get_location_from_gemini(caption_text, GEMINI_API_KEY)
                    if GEMINI_API_KEY and caption_text.strip():
                         time.sleep(0.6)

                    row_data = {
                        'Reel URL': reel_url, 'Caption': caption_text,
                        'Place Name': location_info.get('place_name'), 'City': location_info.get('city'),
                        'State': location_info.get('state'), 'Country': location_info.get('country') 
                    }
                    writer.writerow(row_data) # Append new row
                    existing_reel_urls.add(reel_url) # Add to set to avoid processing duplicates within the same run (if API sends them)
                    new_items_fetched_this_run +=1
                    print(f"Appended to CSV: URL: {reel_url}, Place: {location_info.get('place_name')}, City: {location_info.get('city')}, State: {location_info.get('state')}, Country: {location_info.get('country')}")

                if not data.get("more_available", False):
                    print("Instagram API indicates no more items available.")
                    break
                max_id = data.get("next_max_id", "")
                if not max_id:
                    print("No next_max_id found from Instagram, stopping pagination.")
                    break
    except IOError as e:
        print(f"Error opening or writing to CSV file '{csv_filename}': {e}")
        return None # Indicate failure


    print(f"\nData fetching complete. {new_items_fetched_this_run} new items appended to '{csv_filename}'.")
    return fieldnames


def sort_csv_file(filename: str, fieldnames: list, sort_by_keys: list):
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Ensure all rows are read, even if file was empty before sorting
            if not reader.fieldnames: # Handles empty file or file with only header that got cleared
                print(f"CSV file '{filename}' is empty or has no data rows to sort.")
                return
            data = list(reader)
            if not data:
                print(f"No data rows found in '{filename}' to sort.")
                return


        def sort_key_func(row):
            return tuple(str(row.get(key) or '').lower() for key in sort_by_keys)

        data.sort(key=sort_key_func)

        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"CSV file '{filename}' sorted successfully by {', '.join(sort_by_keys)}.")

    except FileNotFoundError:
        print(f"Error: CSV file '{filename}' not found for sorting.")
    except Exception as e:
        print(f"An error occurred during CSV sorting: {e}")


if __name__ == "__main__":
    if not IG_COOKIES:
        print("Error: IG_COOKIES environment variable not found.")
        exit(1)
    
    if not COLLECTION_ID:
        print("Error: COLLECTION_ID environment variable not found.")
        exit(1)
        
    # MODIFICATION: CSV filename based on COLLECTION_ID
    csv_filename = f"{COLLECTION_NAME}_{COLLECTION_ID}.csv" 

    print(f"Target Instagram Collection ID: {COLLECTION_ID}")
    print(f"Data will be appended to/created at: {csv_filename}")
    if GEMINI_API_KEY:
        print(f"Using Gemini Model: {GEMINI_MODEL_NAME} for location extraction.")
    else:
        print("Warning: GEMINI_API_KEY not found. Location data will not be fetched.")

    all_fieldnames = fetch_collection_posts(COLLECTION_ID, IG_COOKIES, GEMINI_API_KEY, csv_filename)

    if all_fieldnames: 
        sort_keys = ['Country', 'State', 'City']
        print(f"\nAttempting to sort CSV file '{csv_filename}' by {', '.join(sort_keys)}...")
        sort_csv_file(csv_filename, all_fieldnames, sort_keys)
    else:
        print("Skipping CSV sorting as data fetching might have failed or produced no new processable data.")

