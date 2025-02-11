import requests
import os
import pandas as pd
import feedparser
import xml.etree.ElementTree as ET
from tqdm import tqdm
from dotenv import load_dotenv
from datetime import datetime
from importlib import reload
import schedule
import time
#import base64

# Import modules
import rss_feed  # Must define RSS_FEEDS as a list of RSS URLs
from build_dataset import BuildDataset
import extract_raw_data

# Load environment variables
load_dotenv()

# Podchaser API token and endpoint
PODCHASER_API_URL = "https://api.podchaser.com/graphql"
HEADERS_PODCHASER = {
    "Authorization": f"Bearer {os.getenv('Production_Client_Token')}",
    "Content-Type": "application/json"
}

# File paths
INVALID_RSS_ARCHIVE = "invalid_rss_archive.txt"
INVALID_RSS_LOG = "invalid_rss_log.txt"
RSS_FEED_FILE = "rss_feed.py"  # Contains RSS_FEEDS list
EXCEL_FILENAME = "podcasts_data.xlsx"

# Ensure log and archive files exist
for file in [INVALID_RSS_ARCHIVE, INVALID_RSS_LOG]:
    if not os.path.exists(file):
        open(file, "w").close()

print(f"Loaded {len(rss_feed.RSS_FEEDS)} RSS feeds from rss_feed.py")


def log_invalid_rss(rss_url, reason):
    """Log invalid RSS feeds with timestamps and archive them."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {reason}: {rss_url}\n"
    print(f"📌 Logging invalid RSS: {rss_url} - {reason}")
    with open(INVALID_RSS_LOG, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    with open(INVALID_RSS_ARCHIVE, "a", encoding="utf-8") as archive_file:
        archive_file.write(f"{rss_url}\n")

def fetch_podchaser_data():
    """Fetch podcast data from Podchaser API using numeric pagination with 100 items per call (Maximum allowed is 100)."""
    podcasts = []
    page = 0
    while True:
        query = f"""
        {{
            podcasts(first: 100, page: {page}) {{
                data {{
                    id
                    title
                    rssUrl
                    imageUrl
                    language
                    numberOfEpisodes
                    startDate
                    latestEpisodeDate
                    author {{
                        name
                        email
                    }}
                }}
            }}
        }}
        """
        response = requests.post(PODCHASER_API_URL, json={"query": query}, headers=HEADERS_PODCHASER)
        print("Podchaser Status Code:", response.status_code)
        print("Podchaser Response Content:", response.text[:500])
        if response.status_code != 200:
            print(f"❌ Error fetching Podchaser data: {response.status_code} - {response.text}")
            break
        try:
            data = response.json()
            page_data = data.get("data", {}).get("podcasts", {}).get("data", [])
            if not page_data:
                break
            for podcast in page_data:
                if not podcast.get("author", {}).get("email"):
                    continue
                podcasts.append({
                    "id": podcast.get("id", "N/A"),
                    "title": podcast.get("title", "N/A"),
                    "description": "",
                    "url": "",
                    "webUrl": "",
                    "rssUrl": podcast.get("rssUrl", "N/A"),
                    "imageUrl": podcast.get("imageUrl", "N/A"),
                    "language": podcast.get("language", "N/A"),
                    "numberOfEpisodes": podcast.get("numberOfEpisodes", 0),
                    "startDate": podcast.get("startDate", "N/A"),
                    "latestEpisodeDate": podcast.get("latestEpisodeDate", "N/A"),
                    "categories": None,
                    "author_name": podcast.get("author", {}).get("name", "N/A"),
                    "author_email": podcast.get("author", {}).get("email", "N/A"),
                    "source": "Podchaser"
                })
            if len(page_data) < 100:
                break
            page += 1
        except Exception as e:
            print("❌ Error parsing Podchaser JSON response:", str(e))
            break
    return podcasts


### Helper functions for RSS data

def fetch_rss_feed_data(feed_urls):
    """Extract podcast metadata from RSS feeds, including itunes:email."""
    podcasts = []
    invalid_feeds = []
    for feed in tqdm(feed_urls, desc="Fetching RSS Feeds"):
        parsed_feed = feedparser.parse(feed)
        try:
            response = requests.get(feed, timeout=10)
            response.raise_for_status()
            raw_xml = response.text
            root = ET.fromstring(raw_xml)
            namespace = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
            email = root.find(".//itunes:owner/itunes:email", namespace)
            author_email = email.text.strip() if email is not None else None
        except Exception as e:
            print(f"❌ Failed to extract email from {feed}: {e}")
            author_email = None
        print(f"📡 Feed: {feed} - Extracted Email: {author_email}")
        if not author_email or author_email.lower() in ["n/a", "nan", "none", "", "null"]:
            log_invalid_rss(feed, "Missing or invalid email")
            invalid_feeds.append(feed)
            continue
        podcasts.append({
            "id": "N/A",
            "title": parsed_feed.feed.get("title", "N/A"),
            "description": parsed_feed.feed.get("description", "N/A"),
            "url": parsed_feed.feed.get("link", "N/A"),
            "webUrl": parsed_feed.feed.get("link", "N/A"),
            "rssUrl": feed,
            "imageUrl": parsed_feed.feed.get("image", {}).get("href", "N/A"),
            "language": parsed_feed.feed.get("language", "N/A"),
            "numberOfEpisodes": len(parsed_feed.entries),
            "latestEpisodeDate": parsed_feed.entries[0].get("published", "N/A") if parsed_feed.entries else "N/A",
            "author_name": parsed_feed.feed.get("author", "N/A"),
            "author_email": author_email,
            "source": "RSS Feed"
        })
    remove_invalid_feeds(invalid_feeds)
    return podcasts

def remove_invalid_feeds(feeds):
    """Remove invalid RSS feeds from rss_feed.py and reload the module."""
    if not feeds:
        return
    with open(RSS_FEED_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()
    with open(RSS_FEED_FILE, "w", encoding="utf-8") as file:
        for line in lines:
            if not any(feed in line for feed in feeds):
                file.write(line)
    print(f"✅ Invalid RSS feeds removed from {RSS_FEED_FILE}.")
    reload(rss_feed)

### Build legacy data using iTunes (alphabetical approach) and update RSS feeds from raw data

def build_legacy_data():
    """
    Build legacy podcast data using BuildDataset (alphabetical approach)
    and update the RSS feed list from raw data extraction.
    """
    legacy_data = []
    try:
        builder = BuildDataset(mode="alphabet")
        legacy_df = builder.build_data()
        if "Name" in legacy_df.columns:
            legacy_df = legacy_df.rename(columns={"Name": "title", "Feed URL": "rssUrl"})
        if "author_email" in legacy_df.columns:
            legacy_df["author_email"] = legacy_df["author_email"].astype(str).str.strip()
            legacy_df = legacy_df[~legacy_df["author_email"].isin(["N/A", "nan", "None", "", "NaN"])].dropna(subset=["author_email"])
        legacy_data = legacy_df.to_dict(orient="records")
        print(f"Legacy data built with {len(legacy_data)} records.")
    except Exception as e:
        print(f"❌ Error building legacy data: {e}")
        legacy_data = []
    try:
        new_rss_urls = extract_raw_data.extract_rss_urls_from_raw()
        print(f"Extracted {len(new_rss_urls)} new RSS URLs from raw data.")
        updated_feeds = set(rss_feed.RSS_FEEDS)
        for url in new_rss_urls:
            if url not in updated_feeds:
                updated_feeds.add(url)
        with open(RSS_FEED_FILE, "w", encoding="utf-8") as f:
            f.write("RSS_FEEDS = [\n")
            for url in sorted(updated_feeds):
                f.write(f'    "{url}",\n')
            f.write("]\n")
        reload(rss_feed)
        print(f"rss_feed.py updated with {len(updated_feeds)} RSS feeds.")
    except Exception as e:
        print(f"❌ Error updating RSS feeds from raw data: {e}")
    return legacy_data

### Build full database from all sources

def build_full_database():
    """Combine Podchaser, RSS, legacy, Spotify, and data to build the full podcast database."""
    podchaser_data = fetch_podchaser_data()
    rss_data = fetch_rss_feed_data(rss_feed.RSS_FEEDS)
    legacy_data = build_legacy_data()
    full_data = podchaser_data + rss_data + legacy_data
    print(f"Full database built with {len(full_data)} records.")
    return full_data


### Save data to Excel

def save_to_excel(data, filename=EXCEL_FILENAME):
    """Save podcast data to Excel, ensuring rows without valid emails are removed and 'id' is the first column."""
    new_df = pd.DataFrame(data)
    new_df["author_email"] = new_df["author_email"].astype(str).str.strip()
    new_df = new_df[~new_df["author_email"].isin(["N/A", "nan", "None", "", "NaN"])].dropna(subset=["author_email"])
    if os.path.exists(filename):
        existing_df = pd.read_excel(filename, engine="openpyxl")
        existing_df["author_email"] = existing_df["author_email"].astype(str).str.strip()
        existing_df = existing_df[~existing_df["author_email"].isin(["N/A", "nan", "None", "", "NaN"])].dropna(subset=["author_email"])
        combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=["rssUrl", "title"], keep="last")
    else:
        combined_df = new_df
    if "id" in combined_df.columns:
        columns_order = ["id"] + [col for col in combined_df.columns if col != "id"]
        combined_df = combined_df[columns_order]
    with pd.ExcelWriter(filename, engine="openpyxl", mode="w") as writer:
        combined_df.to_excel(writer, index=False)
    print(f"✅ Data updated and saved to {filename}. Total valid records: {len(combined_df)}")

### Automation function

def automate_database_build():
    """Automate the full database build process on a schedule (e.g., daily at 03:00 AM)."""
    def job():
        print(f"⏰ Database build started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        full_data = build_full_database()
        save_to_excel(full_data)
        print(f"⏰ Database build completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    schedule.every().day.at("03:00").do(job)
    print("✅ Automation setup complete. Waiting for scheduled runs...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    full_data = build_full_database()
    save_to_excel(full_data)
    # To enable automation, uncomment the following line:
    # automate_database_build()
