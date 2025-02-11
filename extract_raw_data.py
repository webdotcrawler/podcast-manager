# extract_raw_data.py
import os
import json

RAW_DATA_DIR = "raw_data"

def load_all_raw_data():
    """Load all JSON files from the RAW_DATA_DIR and return a list of JSON objects."""
    all_data = []
    if not os.path.exists(RAW_DATA_DIR):
        return all_data
    for fname in os.listdir(RAW_DATA_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(RAW_DATA_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_data.append(data)
            except Exception as e:
                print(f"Error loading {fname}: {e}")
    return all_data

def extract_rss_urls_from_raw():
    """Extract unique RSS feed URLs from all raw JSON files."""
    all_data = load_all_raw_data()
    rss_urls = set()
    for dataset in all_data:
        for result in dataset.get("results", []):
            feed = result.get("feedUrl")
            if feed:
                rss_urls.add(feed)
    return list(rss_urls)

if __name__ == "__main__":
    urls = extract_rss_urls_from_raw()
    print("Extracted RSS URLs:")
    for url in urls:
        print(url)
