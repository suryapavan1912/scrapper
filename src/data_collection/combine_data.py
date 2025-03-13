#!/usr/bin/env python3
"""
Data Combiner for Mental Health Resources
This script combines data from multiple sources (Yelp and Google Places)
to create a comprehensive dataset for mental health resources.
"""

import os
import json
import argparse
import glob
import pandas as pd
from datetime import datetime

def load_json_files(directory, pattern):
    """
    Load all JSON files matching a pattern in a directory.
    
    Args:
        directory (str): Directory to search in
        pattern (str): Glob pattern to match files
        
    Returns:
        list: List of dictionaries, each containing data from a JSON file
    """
    files = glob.glob(os.path.join(directory, pattern))
    data = []
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                source = 'yelp' if 'yelp_' in os.path.basename(file) else 'google'
                data.append({
                    'source': source,
                    'filename': os.path.basename(file),
                    'data': file_data
                })
                print(f"Loaded {len(file_data)} records from {file}")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return data

def normalize_yelp_data(yelp_data):
    """
    Normalize data from Yelp API to a common format.
    
    Args:
        yelp_data (list): List of business data from Yelp
        
    Returns:
        list: Normalized data
    """
    normalized = []
    
    for business in yelp_data:
        normalized_item = {
            'source': 'yelp',
            'id': business.get('id', ''),
            'name': business.get('name', ''),
            'address': ', '.join(business.get('location', {}).get('display_address', [])),
            'city': business.get('location', {}).get('city', ''),
            'state': business.get('location', {}).get('state', ''),
            'zip_code': business.get('location', {}).get('zip_code', ''),
            'country': business.get('location', {}).get('country', ''),
            'latitude': business.get('coordinates', {}).get('latitude', ''),
            'longitude': business.get('coordinates', {}).get('longitude', ''),
            'phone': business.get('display_phone', ''),
            'website': business.get('url', ''),
            'rating': business.get('rating', ''),
            'review_count': business.get('review_count', ''),
            'price_level': business.get('price', ''),
            'categories': ', '.join([c.get('title', '') for c in business.get('categories', [])]),
            'image_url': business.get('image_url', ''),
            'is_closed': business.get('is_closed', False),
            'hours': business.get('hours', []),
            'attributes': business.get('attributes', {})
        }
        normalized.append(normalized_item)
    
    return normalized

def normalize_google_data(google_data):
    """
    Normalize data from Google Places API to a common format.
    
    Args:
        google_data (list): List of place data from Google
        
    Returns:
        list: Normalized data
    """
    normalized = []
    
    for place in google_data:
        price_level = ''
        if 'price_level' in place:
            # Convert Google's numeric price level to $ symbols
            price_map = {1: '$', 2: '$$', 3: '$$$', 4: '$$$$'}
            price_level = price_map.get(place['price_level'], '')
            
        normalized_item = {
            'source': 'google',
            'id': place.get('place_id', ''),
            'name': place.get('name', ''),
            'address': place.get('formatted_address', ''),
            'city': '',  # Google doesn't provide city separately
            'state': '',
            'zip_code': '',
            'country': '',
            'latitude': place.get('geometry', {}).get('location', {}).get('lat', ''),
            'longitude': place.get('geometry', {}).get('location', {}).get('lng', ''),
            'phone': place.get('formatted_phone_number', ''),
            'website': place.get('website', ''),
            'rating': place.get('rating', ''),
            'review_count': place.get('user_ratings_total', ''),
            'price_level': price_level,
            'categories': ', '.join(place.get('types', [])),
            'image_url': '',  # Google photos require a separate API call
            'is_closed': place.get('business_status', '') != 'OPERATIONAL',
            'hours': place.get('opening_hours', {}).get('weekday_text', []),
            'attributes': {}
        }
        normalized.append(normalized_item)
    
    return normalized

def deduplicate_data(data, match_threshold=0.8):
    """
    Remove duplicate entries across data sources.
    
    This uses a simple name + location matching strategy.
    For a production system, a more sophisticated fuzzy matching might be needed.
    
    Args:
        data (list): List of normalized data items
        match_threshold (float): Similarity threshold for deduplication
        
    Returns:
        list: Deduplicated data
    """
    # For a simple version, we'll just use exact name matching
    # A full implementation would use fuzzy matching based on name and location
    
    unique_places = {}
    
    for item in data:
        name = item['name'].lower()
        lat = item['latitude']
        lng = item['longitude']
        
        # Create a key from name and approximate location
        # This is a simple approach - a production system would use better matching
        key = f"{name}"
        
        # If we have lat/lng, make the key more specific
        if lat and lng:
            # Round to 3 decimal places (roughly 100m precision)
            key = f"{name}_{round(float(lat), 3)}_{round(float(lng), 3)}"
        
        if key in unique_places:
            # We already have this place
            # If the new record is from Google and the existing is from Yelp,
            # or if the new record has more info, replace the existing one
            existing = unique_places[key]
            
            # Prefer the record with more information
            if (item['source'] == 'google' and existing['source'] == 'yelp') or \
               (len(str(item)) > len(str(existing))):
                unique_places[key] = item
                
            # Merge any missing data from the new record into the existing one
            else:
                for field, value in item.items():
                    if not existing.get(field) and value:
                        existing[field] = value
        else:
            # New place
            unique_places[key] = item
    
    return list(unique_places.values())

def combine_data(source_dir='data', output_dir='data'):
    """
    Combine data from multiple sources and save to a file.
    
    Args:
        source_dir (str): Directory containing source data files
        output_dir (str): Directory to save combined data
    """
    # Load all JSON files
    print("Loading Yelp data...")
    yelp_files = load_json_files(source_dir, 'yelp_*.json')
    
    print("Loading Google data...")
    google_files = load_json_files(source_dir, 'google_*.json')
    
    all_data = []
    
    # Normalize data from each source
    for file_data in yelp_files:
        print(f"Normalizing Yelp data from {file_data['filename']}...")
        normalized = normalize_yelp_data(file_data['data'])
        all_data.extend(normalized)
    
    for file_data in google_files:
        print(f"Normalizing Google data from {file_data['filename']}...")
        normalized = normalize_google_data(file_data['data'])
        all_data.extend(normalized)
    
    print(f"Total records before deduplication: {len(all_data)}")
    
    # Deduplicate data
    print("Deduplicating data...")
    deduplicated_data = deduplicate_data(all_data)
    
    print(f"Total records after deduplication: {len(deduplicated_data)}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save combined data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = os.path.join(output_dir, f"combined_data_{timestamp}.json")
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_data, f, indent=2)
    
    # Save as CSV for easy viewing
    csv_filename = os.path.join(output_dir, f"combined_data_{timestamp}.csv")
    df = pd.DataFrame(deduplicated_data)
    df.to_csv(csv_filename, index=False)
    
    print(f"Combined data saved to {json_filename} and {csv_filename}")

def main():
    parser = argparse.ArgumentParser(description='Combine data from multiple sources')
    parser.add_argument('--source', type=str, default='data',
                        help='Directory containing source data files')
    parser.add_argument('--output', type=str, default='data',
                        help='Directory to save combined data')
    
    args = parser.parse_args()
    
    combine_data(args.source, args.output)

if __name__ == "__main__":
    main() 