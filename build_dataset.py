# build_dataset.py
import requests
import pandas as pd
import os
from datetime import datetime
import json
import string
import itertools

RAW_DATA_DIR = "raw_data"

def save_raw_response(term, data):
    """Save raw JSON response to a file for the given search term."""
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(RAW_DATA_DIR, f"{term}_{timestamp}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw data for term '{term}' to {filename}")

def generate_alphabet_combinations(n=1):
    """Generate all n-letter combinations (default n=1 for letters a-z)."""
    if n == 1:
        return list(string.ascii_lowercase)
    else:
        return [''.join(p) for p in itertools.product(string.ascii_lowercase, repeat=n)]

class BuildDataset:
    """
    A legacy data builder that uses the iTunes Search API to collect podcast data.
    
    The default mode is "alphabet", which generates search terms from the letters a–z.
    You may increase the combination length (n) to get more granular queries.
    """
    def __init__(self, mode="alphabet", terms=None, n=1):
        if mode == "alphabet":
            # If terms are provided, use them; otherwise, generate n-letter combinations.
            if terms is None:
                self.terms = generate_alphabet_combinations(n=n)
            else:
                self.terms = terms
        else:
            self.terms = terms if terms is not None else []
        self.rows = []  # List to hold each podcast's data as a dictionary

    def build_data(self):
        base_url = "https://itunes.apple.com/search"
        for term in self.terms:
            params = {
                "term": term,
                "limit": 200,  # Maximum results per query
                "country": "US",
                "entity": "podcast"
            }
            try:
                response = requests.get(base_url, params=params)
                data = response.json()
                save_raw_response(term, data)
                result_count = data.get("resultCount", 0)
                print(f"Term '{term}': {result_count} results")
                for result in data.get("results", []):
                    row = {
                        "Name": result.get("collectionName", "N/A"),
                        "Artwork": result.get("artworkUrl100", "N/A"),
                        "Episode Count": result.get("trackCount", 0),
                        "GenreIDs": ", ".join(map(str, result.get("genreIds", []))) if result.get("genreIds") else "N/A",
                        "iTunes URL": result.get("collectionViewUrl", result.get("trackViewUrl", "N/A")),
                        "rssUrl": result.get("feedUrl", "N/A"),
                        # iTunes API does not provide email contact information
                        "author_email": "N/A"
                    }
                    self.rows.append(row)
            except Exception as e:
                print(f"Error fetching data for term '{term}': {e}")
        legacy_df = pd.DataFrame(self.rows)
        legacy_df.drop_duplicates(inplace=True)
        return legacy_df
