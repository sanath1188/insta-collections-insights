import os
import json
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

# Load collections from the JSON file
with open('collections.json', 'r') as file:
    data = json.load(file)
    collections = data['collections']
    print(collections)

for collection in collections:
    collection_id = collection["id"]
    collection_name = collection["name"]

    # Update the .env file dynamically
    with open('.env', 'r') as file:
        lines = file.readlines()

    with open('.env', 'w') as file:
        for line in lines:
            if line.startswith("COLLECTION_ID="):
                file.write(f'COLLECTION_ID="{collection_id}"\n')
            elif line.startswith("COLLECTION_NAME="):
                file.write(f'COLLECTION_NAME="{collection_name}"\n')
            else:
                file.write(line)

    # Run the collect.py script and wait for it to finish
    print(f"Running collection: {collection_name} (ID: {collection_id})")
    result = subprocess.run(["python", "collect.py"])

    # Check if the script ran successfully
    if result.returncode != 0:
        print(f"Error occurred while processing collection: {collection_name}. Exiting.")
        break

    # Wait for 5 seconds before processing the next collection
    print("Waiting for 10 seconds before the next collection...")
    time.sleep(10)

print("All collections have been processed.")