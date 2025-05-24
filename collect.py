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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

def fetch_collection_posts(collection_id, cookies_header, gemini_key, csv_filename):
    if not collection_id:
        print("Error: COLLECTION_ID is not set.")
        return

    base_url = f"https://www.instagram.com/api/v1/feed/collection/{collection_id}/posts/"
    max_id = ""
    session = requests.Session()

    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
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
        "x-csrftoken": "",
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "",
        "x-requested-with": "XMLHttpRequest",
        "x-web-session-id": "",
    }

    def extract_cookie_value(cookie_str, key):
        if not cookie_str: return ""
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith(key + "="):
                return part[len(key)+1:]
        return ""

    csrftoken = extract_cookie_value(cookies_header, "csrftoken")
    if not csrftoken:
        print("Warning: csrftoken not found in cookies. This might lead to issues with Instagram API.")
    headers["x-csrftoken"] = csrftoken

    insta_cookies = {}
    if cookies_header:
        for cookie_part in cookies_header.split(";"):
            if "=" in cookie_part:
                k, v = cookie_part.strip().split("=", 1)
                insta_cookies[k] = v
    session.cookies.update(insta_cookies)

    # Fieldnames defined once, used by DictWriter and sorter
    fieldnames = ['Reel URL', 'Caption', 'Place Name', 'City', 'State', 'Country']

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        page_count = 0
        item_count = 0
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
                if max_id == "":
                     print("No items found in the Instagram collection or collection is private/invalid.")
                else:
                     print("No more items to fetch from Instagram.")
                break

            for item_data in items:
                item_count += 1
                media = item_data.get("media", {})
                code = media.get("code")
                caption_obj = media.get("caption", {})
                caption_text = caption_obj.get("text", "") if caption_obj else ""
                reel_url = f"https://www.instagram.com/reel/{code}/" if code else "Unknown URL"
                
                print(f"\nProcessing Instagram item {item_count}: {reel_url}")

                location_info = get_location_from_gemini(caption_text, GEMINI_API_KEY)
                if GEMINI_API_KEY and caption_text.strip():
                     time.sleep(0.6)

                row_data = {
                    'Reel URL': reel_url,
                    'Caption': caption_text,
                    'Place Name': location_info.get('place_name'),
                    'City': location_info.get('city'),
                    'State': location_info.get('state'),
                    'Country': location_info.get('country') 
                }
                writer.writerow(row_data)
                print(f"Saved to CSV: URL: {reel_url}, Place: {location_info.get('place_name')}, City: {location_info.get('city')}, State: {location_info.get('state')}, Country: {location_info.get('country')}")

            if not data.get("more_available", False):
                print("Instagram API indicates no more items available.")
                break

            max_id = data.get("next_max_id", "")
            if not max_id:
                print("No next_max_id found from Instagram, stopping pagination.")
                break
            # time.sleep(0.5)

    print(f"\nData fetching complete. {item_count} items processed. Output saved to {csv_filename}")
    return fieldnames # Return fieldnames for sorter


# MODIFICATION: New function to sort the CSV file
def sort_csv_file(filename: str, fieldnames: list, sort_by_keys: list):
    """
    Sorts a CSV file by the specified keys.
    Handles None values by treating them as empty strings for sorting.
    """
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Sort data: Treat None as empty string '' for sorting to avoid type errors
        # and ensure consistent sorting (None/empty usually comes first).
        def sort_key_func(row):
            return tuple(str(row.get(key) or '').lower() for key in sort_by_keys)
            # Using .lower() for case-insensitive sorting of location names

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
        
    csv_filename = f"instagram_collection_{COLLECTION_ID}_posts.csv" 

    print(f"Fetching posts for Instagram Collection ID: {COLLECTION_ID}")
    print(f"Output will be saved to: {csv_filename}")
    if GEMINI_API_KEY:
        print(f"Using Gemini Model: {GEMINI_MODEL_NAME} for location extraction.")
    else:
        print("Warning: GEMINI_API_KEY not found. Location data will not be fetched.")

    # Fetch posts and get fieldnames
    all_fieldnames = fetch_collection_posts(COLLECTION_ID, IG_COOKIES, GEMINI_API_KEY, csv_filename)

    # MODIFICATION: Sort the CSV file after fetching
    if all_fieldnames: # Ensure fetch_collection_posts ran and returned fieldnames
        sort_keys = ['Country', 'State', 'City']
        print(f"\nAttempting to sort CSV file by {', '.join(sort_keys)}...")
        sort_csv_file(csv_filename, all_fieldnames, sort_keys)
    else:
        print("Skipping CSV sorting as data fetching might have failed or produced no data.")
