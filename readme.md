## Setup

1.  **Clone the repository (if applicable) or download `collect.py`.**

2.  **Create a `.env` file** in the same directory as `collect.py` with the following content:

    ```
    IG_COOKIES="your_full_instagram_cookie_string_here"
    COLLECTION_ID="your_instagram_collection_id_here"
    COLLECTION_NAME="YourCollectionNameHere"
    GEMINI_API_KEY="your_google_gemini_api_key_here"
    ```

3.  **Populate `.env` variables**:

    - **`IG_COOKIES`**: Your full Instagram cookie string.

      - **How to get**:
        1.  Open Instagram in your web browser (e.g., Chrome).
        2.  Log in to your account.
        3.  Open Developer Tools (usually by pressing F12 or right-clicking and selecting "Inspect").
        4.  Go to the "Network" tab.
        5.  Filter for requests to the Instagram API (e.g., fetch any page or interact with the site).
        6.  Find a request to an Instagram endpoint (e.g., one for loading posts).
        7.  In the "Headers" section of the request, find the "Request Headers" and look for the `cookie:` entry.
        8.  Copy the entire string value of the `cookie:` header. This is your `IG_COOKIES` value. It will be a long string of `key=value;` pairs.
            _Alternatively, you can copy the request as cURL and extract the cookie string from the `-b` or `--cookie` argument._

    - **`COLLECTION_ID`**: The numerical ID of the Instagram collection you want to process.

      - **How to get**:
        1.  Navigate to your saved posts on Instagram (Profile -> Saved).
        2.  Click on the specific collection.
        3.  The URL in your browser will look something like: `https://www.instagram.com/yourusername/saved/yourcollectionname/18012345678901234/`.
        4.  The long number at the end (e.g., `18012345678901234`) is the `COLLECTION_ID`.

    - **`COLLECTION_NAME`**: A descriptive name for your collection (e.g., "TravelFood", "Architecture"). This will be used in the output CSV filename. Avoid spaces or special characters that are problematic in filenames; use underscores or hyphens if needed.

    - **`GEMINI_API_KEY`**: Your API key for Google's Gemini API.
      - You can obtain this from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

Once the prerequisites are met and the `.env` file is correctly configured, run the script from your terminal:

```
python collect.py
```

The script will:

1.  Print the target Collection ID and the output CSV filename.
2.  Attempt to read existing Reel URLs from the CSV if it exists.
3.  Fetch posts from the specified Instagram collection.
4.  For each new post:
    - Send its caption to the Gemini API for location analysis.
    - Print the extracted location information.
    - Append the post details (Reel URL, Caption, Place Name, City, State, Country) to the CSV file.
5.  After processing all posts for the current run, it will sort the entire CSV file.

## Output

The script generates/updates a CSV file named `<COLLECTION_NAME>_<COLLECTION_ID>.csv` in the same directory. For example, if `COLLECTION_NAME` is `MyAdventures` and `COLLECTION_ID` is `12345`, the file will be `MyAdventures_12345.csv`.

The CSV file contains the following columns:

- **Reel URL**: The direct URL to the Instagram post/reel.
- **Caption**: The full caption of the post.
- **Place Name**: The specific name of the location/venue (e.g., "Eiffel Tower", "Central Park Cafe").
- **City**: The city where the place is located.
- **State**: The state, province, or region.
- **Country**: The country where the place is located.

## Script Details (`collect.py`)

The `collect.py` script performs the following main operations:

1.  **Environment Setup**: Loads API keys and configuration from the `.env` file.
2.  **Gemini API Interaction (`get_location_from_gemini`)**:
    - Constructs a request to the Gemini API with the post caption and a specific system instruction.
    - Defines an expected JSON schema for the response to guide location extraction.
    - Handles API responses and potential errors.
3.  **Instagram Data Fetching & CSV Handling (`fetch_collection_posts`)**:
    - Reads existing Reel URLs from the output CSV to prevent duplicates.
    - Paginates through the Instagram collection API to get all posts.
    - For each new post:
      - Calls `get_location_from_gemini` for location analysis.
      - Appends the new data to the CSV file. The CSV is opened in append mode (`a+`), and the header is written only if the file is new/empty.
4.  **CSV Sorting (`sort_csv_file`)**:
    - Reads the entire CSV file.
    - Sorts the data in memory by Country, then State, then City (case-insensitively).
    - Overwrites the CSV file with the sorted data.
5.  **Main Execution Block**: Coordinates the fetching and sorting processes.

## Important Notes

- **Instagram API Changes**: Instagram's private API endpoints can change without notice. If the script stops working, the Instagram API calls might need an update (headers, endpoint URL, etc.).
- **Rate Limiting**: Both Instagram and Gemini APIs have rate limits. If you process very large collections or run the script too frequently, you might encounter temporary blocks. The script includes small delays (`time.sleep`) to mitigate this, but they can be adjusted.
- **Cookie Expiration**: Instagram cookies expire. If you start getting authentication errors, you'll need to update the `IG_COOKIES` value in your `.env` file.
- **Gemini API Quotas & Billing**: Be mindful of your Gemini API usage, as it might be subject to quotas and associated costs depending on your Google Cloud project setup and usage volume.
