# Podcast Manager

This project is an integrated solution for building and maintaining a comprehensive podcast database. It collects and merges data from multiple sources, including:

- **Podchaser API:** Retrieves fresh podcast data with numeric pagination (up to 100 items per call).
- **iTunes Data:** Uses an alphabetical querying approach (iterating over A–Z or multi-letter combinations) to fetch podcast data via the iTunes Search API. Raw JSON responses are archived in the `raw_data` folder for further processing.
- **RSS Feeds:** Extracts and validates podcast metadata from RSS feeds. Invalid feeds (e.g., missing valid email addresses) are logged and removed from the feed list.

The final merged data is saved as an Excel file (`podcasts_data.xlsx`) containing deduplicated records with valid contact information. An optional automation feature is available to schedule daily database builds.

## Features

- **Comprehensive Data Collection:**  
  Combines data from Podchaser, iTunes (alphabetical queries), and RSS feeds.
  
- **Raw Data Archiving:**  
  Saves raw iTunes JSON responses in a dedicated `raw_data` folder for archival and reprocessing.
  
- **Dynamic RSS Feed Management:**  
  Extracts unique RSS feed URLs from the raw data and automatically updates the RSS feed list (`rss_feed.py`).
  
- **Data Merging and Deduplication:**  
  Merges data from multiple sources, filters out records without valid email addresses, and removes duplicates.
  
- **Automation:**  
  Uses the `schedule` package to run the full build process daily at a specified time.
----------------------------------------------------------------
## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/podcast-database-builder.git
   cd podcast-database-builder


----------------------------------------------------------------
2. **Create a virtual environment and install dependencies:**

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

----------------------------------------------------------------
3. **Set up environment variables:**

Create a .env file in the root directory with the following key:

Production_Client_Token=your_podchaser_api_token

----------------------------------------------------------------
4. **Update the RSS Feed List:**

Ensure you have a file named rss_feed.py in the repository root that defines a list of RSS feed URLs. For example:

# rss_feed.py
RSS_FEEDS = [
    "https://rss.art19.com/the-daily"
]
----------------------------------------------------------------
#### Usage

Building the Database

Run the main integration script to fetch, merge, and save the podcast data:

python fetch.py

----------------------------------------------------------------
This script will:

    Fetch data from Podchaser (up to 100 results per call).
    Extract and validate podcast data from the RSS feeds defined in rss_feed.py.
    Build legacy podcast data from iTunes by iterating over the alphabet (A–Z) and archiving raw JSON responses in the raw_data folder.
    Merge all data sources and save the deduplicated dataset to podcasts_data.xlsx.

Automation

To schedule daily database builds (e.g., at 03:00 AM), uncomment the automate_database_build() call at the end of fetch.py:

# automate_database_build()

Then run the script; it will execute the build process automatically on the scheduled time.
-----------------------------------------------------------------

#### File Structure

├── build_dataset.py        # Legacy data extraction module (iTunes alphabetical querying)

├── extract_raw_data.py     # Module to load raw iTunes JSON responses and extract unique RSS URLs

├── fetch.py                # Main integration script to build and merge the podcast database

├── rss_feed.py             # Defines the list of RSS feed URLs

├── raw_data/               # Directory for archived raw iTunes JSON responses

├── .env                    # Environment configuration file (not committed)

└── README.md               # This file

