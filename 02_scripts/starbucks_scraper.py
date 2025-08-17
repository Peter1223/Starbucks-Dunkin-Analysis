# starbucks_scraper.py
import requests
import json
import pandas as pd
import time
import os

def parse_store_data(store_data):
    # The actual store details are nested inside the 'store' key
    store = store_data.get('store', {})
    address = store.get('address', {})
    coordinates = store.get('coordinates', {})
    
    return {
        'store_id': store.get('id'),
        'store_number': store.get('storeNumber'),
        'name': store.get('name'),
        'ownership_type': store.get('ownershipTypeCode'),
        'street_address': address.get('streetAddressLine1'),
        'city': address.get('city'),
        'state': address.get('countrySubdivisionCode'),
        'postal_code': address.get('postalCode'),
        'latitude': coordinates.get('latitude'),
        'longitude': coordinates.get('longitude'),
        'phone_number': store.get('phoneNumber')
    }

def main():
    
    # Main function to scrape all Starbucks locations in the US.
    
    #  SETUP
    zip_code_file = './01_data/uszips.csv'
    output_file = './01_data/starbucks_us_locations.csv'
    
    if not os.path.exists(zip_code_file):
        print(f"Error: Zip code file not found at {zip_code_file}")
        print("Please download it from https://simplemaps.com/data/us-zips and place it in the '01_data' folder.")
        return

    df_zips = pd.read_csv(zip_code_file)
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.starbucks.com/store-locator',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    all_stores_data = []
    # Use a set for efficient checking of duplicates
    seen_store_ids = set() 
    
    total_zips = len(df_zips)
    print(f"Starting to scrape Starbucks locations for {total_zips} zip codes...")

    # MAIN SCRAPING LOOP 
    for index, row in df_zips.iterrows():
        lat, lng = row['lat'], row['lng']
        url = f"https://www.starbucks.com/apiproxy/v1/locations?lat={lat}&lng={lng}&limit=100" # Ask for up to 100 stores
        
        # Print progress
        print(f"Progress: {index + 1}/{total_zips} | Querying for Zip {row['zip']} ({lat:.2f}, {lng:.2f})...", end="")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            stores_found = 0
            if data:
                for store_data in data:
                    store_id = store_data.get('store', {}).get('id')
                    if store_id and store_id not in seen_store_ids:
                        all_stores_data.append(parse_store_data(store_data))
                        seen_store_ids.add(store_id)
                        stores_found += 1
            
            print(f" Found {len(data)} stores nearby, added {stores_found} new stores.")

            # Wait a little bit between requests to not hammer the server.
            time.sleep(0.1) 

        except requests.exceptions.RequestException as e:
            print(f" Error: {e}")
        except json.JSONDecodeError:
            print(" Failed to decode JSON.")

    #  SAVE RESULTS 
    print(f"\nScraping complete. Found a total of {len(all_stores_data)} unique stores.")
    df_final = pd.DataFrame(all_stores_data)
    df_final.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    main()