# Instagram Collection Exporter & AI-Powered Location Analyzer

**A Python tool to download posts from your Instagram collections, use Google Gemini to extract detailed location data (place, city, state, country) from captions, and save everything to a sortable, appendable CSV file.**

This script fetches posts from a specified Instagram collection, extracts location information using Google's Gemini API, and saves the data to a CSV file. It's designed to be run multiple times, efficiently appending only new, unique posts to the CSV and skipping those already processed. The output CSV is named using your collection's name and ID (e.g., `MyTravels_1234567890.csv`) and is automatically sorted by Country, State, and City after each run.

## Features

- **Fetches Instagram Collection Posts**: Retrieves all posts from a specified Instagram collection using its ID.
- **AI-Powered Location Extraction**: Utilizes Google's Gemini API (model `gemini-1.5-pro-latest`) to analyze post captions and extract:
  - Specific Place Name (e.g., restaurant, landmark)
  - City
  - State/Region
  - Country
- **Smart Location Inference**: The Gemini prompt is engineered to intelligently infer missing location details (e.g., determine the state from a city, or identify a city and state if a local area like "Jayanagar" is mentioned).
- **Dynamic CSV Output**: Saves extracted data into a CSV file named `<COLLECTION_NAME>_<COLLECTION_ID>.csv` (e.g., `TravelPhotos_18012345678901234.csv`).
- **Incremental Updates & Deduplication**:
  - If the CSV file already exists, the script appends new, unique posts.
  - It intelligently checks for existing 'Reel URLs' in the CSV to avoid redundant processing and unnecessary Gemini API calls, saving time and resources.
  - If the CSV file doesn't exist, it creates a new one with appropriate headers.
- **Automatic Data Sorting**: After each successful run, the entire CSV file is sorted by Country, then State, then City (case-insensitively) for easy review and analysis.
- **Secure Configuration**: Leverages a `.env` file for managing sensitive credentials (API keys, cookies) and collection parameters, keeping them separate from the codebase.

## Prerequisites

- Python 3.7+
- The following Python libraries:
  - `requests` (for making HTTP requests)
  - `python-dotenv` (for managing environment variables)

You can install these essential libraries using pip:

```bash
pip install -r requirements.txt
```

## Setup Instructions

1.  **Clone the Repository or Download `collect.py`**:
    If this script is part of a Git repository, clone it. Otherwise, download the `collect.py` file to your local machine.

2.  **Create and Configure the `.env` File**:
    In the same directory as `collect.py`, create a file named `.env`. Add the following lines to this file, replacing the placeholder values with your actual information. Use .env.sample for easy setup.

    ```
    IG_COOKIES="your_full_instagram_cookie_string_here"
    #Leave the collection vars empty here.
    COLLECTION_ID=""
    COLLECTION_NAME=""
    GEMINI_API_KEY="your_google_gemini_api_key_here"
    ```

3.  **Populate `.env` Variables**:

    - **`IG_COOKIES`**: Your complete Instagram session cookie string.

      - **How to obtain**:
        1.  Open Instagram in your web browser (e.g., Chrome, Firefox).
        2.  Log in to your Instagram account.
        3.  Open your browser's Developer Tools (usually by pressing F12, or right-click -> "Inspect").
        4.  Navigate to the "Network" tab.
        5.  Refresh the Instagram page or perform an action (like viewing a post) to generate network requests.
        6.  Look for a request to an Instagram API endpoint (e.g., `graphql/query`, or any request to `www.instagram.com`).
        7.  Select the request. In the "Headers" section (often under "Request Headers"), find the `cookie:` entry.
        8.  Copy the **entire string value** associated with the `cookie:` header. This value is what you need for `IG_COOKIES`. It will be a long string containing multiple `key=value;` pairs.
            _Tip: Some browsers offer a "Copy as cURL" option for requests. You can paste this into a text editor and extract the cookie string from the `-b` or `--cookie` argument._

    - **`GEMINI_API_KEY`**: Your API key for accessing Google's Gemini API.
      - You can generate an API key from [Google AI Studio](https://aistudio.google.com/app/apikey) by creating a new project if needed.

4.  **Create a `collections.json` File**:
    Create a `collections.json` file in the same directory with the following structure:

    ```json
    {
    	"collections": [
    		{ "id": "your_instagram_collection_id_1", "name": "CollectionName1" },
    		{ "id": "your_instagram_collection_id_2", "name": "CollectionName2" }
    		// Add more collections as needed
    	]
    }
    ```

    - **`id`**: The unique numerical identifier for the Instagram collection you wish to process.

      - **How to obtain**:
        1.  On Instagram's website, go to your profile page.
        2.  Click on the "Saved" tab (bookmark icon).
        3.  Open the specific collection you want to target.
        4.  Observe the URL in your browser's address bar. It will typically look like: `https://www.instagram.com/your_username/saved/your_collection_name/18012345678901234/`.
        5.  The long number at the end (e.g., `18012345678901234`) is the `id`.

    - **`name`**: A descriptive name for your collection (e.g., `TravelEurope`, `FoodieFinds`, `ArchitectureInspirations`). This name will be part of the output CSV filename. **Important**: Use a name that is safe for filenames (avoid spaces, slashes, and other special characters; underscores or hyphens are good alternatives).

## Usage

After setting up the prerequisites and configuring your `.env` file, you can run the script from your terminal:

```
python run_collections.py
```

The script will then:

1.  Loop over all collections you've mentioned in the collections.json file.
2.  Display the target Instagram Collection ID and the name of the CSV file it will be working with.
3.  If the CSV file exists, it will read previously processed Reel URLs to avoid duplication.
4.  Begin fetching posts from the specified Instagram collection page by page.
5.  For each newly encountered post:
    - If its Reel URL is not already in the CSV, it will send the post's caption to the Gemini API for location analysis.
    - Log the extracted location details (Place Name, City, State, Country).
    - Append the post's information to the CSV file.
    - If a post is already in the CSV, it will be skipped.
6.  Once all new posts for the current run have been processed and appended, the script will sort the entire CSV file by Country, then State, then City.

## Output File

The script generates or updates a CSV file in the same directory. The filename will be `<COLLECTION_NAME>_<COLLECTION_ID>.csv`. For instance, if your `COLLECTION_NAME` is `EuropeanAdventures` and `COLLECTION_ID` is `12345`, the output file will be named `EuropeanAdventures_12345.csv`.

This CSV file will contain the following columns:

- `Reel URL`: The direct URL to the Instagram post or reel.
- `Caption`: The complete text caption of the post.
- `Place Name`: The specific name of the location or venue identified (e.g., "Louvre Museum", "Joe's Pizza").
- `City`: The city where the location is identified.
- `State`: The state, province, or region.
- `Country`: The country where the location is identified.

## Script Breakdown (`collect.py`)

The Python script is structured with several key functions:

1.  **Environment Configuration**: At startup, it loads API keys, cookies, and collection details from the `.env` file.
2.  **Gemini API Interaction (`get_location_from_gemini`)**:
    - This function is responsible for communicating with the Google Gemini API.
    - It constructs a carefully worded "system instruction" (prompt) to guide the AI in extracting location data accurately and inferring missing details.
    - It defines an expected JSON schema for the API's response to ensure structured output.
    - Includes error handling for API requests and response parsing.
3.  **Instagram Data Fetching & CSV Management (`fetch_collection_posts`)**:
    - The core function for interacting with Instagram and managing the CSV data.
    - **Deduplication**: Before fetching, it reads all 'Reel URL' values from an existing CSV file (if present) into a set for efficient duplicate checking.
    - **API Pagination**: It iterates through the Instagram collection's API pages to retrieve all posts.
    - **Conditional Processing**: For each post, it checks if the Reel URL has already been processed.
      - If new, it calls `get_location_from_gemini`.
      - The new data (post URL, caption, and extracted locations) is then appended to the CSV.
    - **CSV Creation/Appending**: The CSV file is opened in append mode (`a+`). The header row is written only if the file is new or was previously empty.
4.  **CSV Sorting (`sort_csv_file`)**:
    - This utility function is called after all new data for a run has been appended.
    - It reads the entire content of the CSV file into memory.
    - Sorts the data based on 'Country', then 'State', then 'City' columns (case-insensitively).
    - Overwrites the original CSV file with the newly sorted data.
5.  **Main Execution (`if __name__ == "__main__":`)**:
    - Orchestrates the overall process: sets up filenames, calls `fetch_collection_posts`, and then calls `sort_csv_file`.

## Important Considerations

- **Instagram API Stability**: Instagram's internal API endpoints (used by this script for fetching collection data) are not officially documented for third-party use and can change without warning. If the script suddenly stops fetching data, it might be due to such changes, requiring updates to API request headers or endpoint URLs.
- **API Rate Limiting**: Both Instagram and the Google Gemini API enforce rate limits to prevent abuse. If you process extremely large collections or run the script very frequently in short bursts, you might encounter temporary throttling or blocks. The script incorporates small delays (`time.sleep`) to be a good API citizen, but these may need adjustment for very high-volume use.
- **Instagram Cookie Expiration**: The `IG_COOKIES` value represents your browser session with Instagram. These cookies expire after some time. If you start encountering authentication-related errors or empty responses from Instagram, you will likely need to refresh your `IG_COOKIES` value in the `.env` file by repeating the "How to obtain" steps.
- **Google Gemini API Quotas & Costs**: Be aware of your Google Gemini API usage. Depending on your Google Cloud project settings and the volume of requests, usage might fall under free tier limits or incur costs. Monitor your usage in the Google Cloud Console.

## Upcoming Features

- **Error Handling Enhancements**: Improve error handling to provide more detailed feedback on failures during data collection.
- **Logging**: Implement logging functionality to keep track of the processing status and any issues encountered during execution.
- **User Interface**: Develop a simple user interface to allow users to manage collections and view results more easily.
- **Data Export Options**: Add functionality to export collected data in various formats (e.g., CSV, JSON) for easier analysis and sharing.
- **Multi-Collection Processing**: Explore options for processing multiple collections in parallel while respecting API rate limits.
