#!/usr/bin/env python3
"""
Data Combiner for Mental Health Resources
This script combines data from the raw_places collection (Yelp and Google Places)
to create a comprehensive dataset in the processed_places collection.
"""

import argparse
from datetime import datetime
from mongo_utils import (
    get_raw_places,
    save_processed_places,
    get_cities_collection
)

def load_data_from_mongodb(city_slug=None, category=None):
    """
    Load data from the raw_places collection with optional filtering.
    
    Args:
        city_slug (str, optional): Filter by city slug
        category (str, optional): Filter by category
        
    Returns:
        list: List of dictionaries containing raw place data
    """
    print(f"Loading raw data from MongoDB...")
    
    # Get all raw places, optionally filtered by city and category
    places = get_raw_places(city_slug=city_slug, category=category)
    
    if city_slug:
        print(f"Loaded {len(places)} raw records for city slug '{city_slug}'")
    else:
        print(f"Loaded {len(places)} raw records from all cities")
    
    # Group by source for processing
    yelp_data = [place for place in places if place.get('source') == 'yelp']
    google_data = [place for place in places if place.get('source') == 'google']
    
    print(f"Found {len(yelp_data)} Yelp records and {len(google_data)} Google records")
    
    return {
        'yelp': yelp_data,
        'google': google_data
    }

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
            'name': business.get('name', ''),
            'address': ', '.join(business.get('location', {}).get('display_address', [])),
            'city_slug': business.get('city_slug', ''),
            'city_name': business.get('city_name', ''),
            'state': business.get('state', ''),
            'state_code': business.get('state_code', ''),
            'zip_code': business.get('location', {}).get('zip_code', ''),
            'country': business.get('location', {}).get('country', ''),
            'location': {
                'type': 'Point',
                'coordinates': [
                    business.get('coordinates', {}).get('longitude', 0),
                    business.get('coordinates', {}).get('latitude', 0)
                ]
            },
            'phone': business.get('display_phone', ''),
            'website': business.get('url', ''),
            'rating': business.get('rating', ''),
            'review_count': business.get('review_count', ''),
            'price_level': business.get('price', ''),
            'category': business.get('category', ''),
            'categories': ', '.join([c.get('title', '') for c in business.get('categories', [])]),
            'image_url': business.get('image_url', ''),
            'is_closed': business.get('is_closed', False),
            'hours': business.get('hours', []),
            'source_ids': {
                'yelp': business.get('yelp_id', business.get('id', ''))
            },
            'sources': ['yelp'],
            'created_at': datetime.now(),
            'updated_at': datetime.now()
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
            'name': place.get('name', ''),
            'address': place.get('formatted_address', ''),
            'city_slug': place.get('city_slug', ''),
            'city_name': place.get('city_name', ''),
            'state': place.get('state', ''),
            'state_code': place.get('state_code', ''),
            'country': place.get('country', 'USA'),
            'location': {
                'type': 'Point',
                'coordinates': [
                    place.get('geometry', {}).get('location', {}).get('lng', 0),
                    place.get('geometry', {}).get('location', {}).get('lat', 0)
                ]
            },
            'phone': place.get('formatted_phone_number', ''),
            'website': place.get('website', ''),
            'rating': place.get('rating', ''),
            'review_count': place.get('user_ratings_total', ''),
            'price_level': price_level,
            'category': place.get('category', ''),
            'categories': ', '.join(place.get('types', [])),
            'image_url': '',  # Google photos require a separate API call
            'is_closed': place.get('business_status', '') != 'OPERATIONAL',
            'hours': place.get('opening_hours', {}).get('weekday_text', []),
            'source_ids': {
                'google': place.get('google_id', place.get('place_id', ''))
            },
            'sources': ['google'],
            'created_at': datetime.now(),
            'updated_at': datetime.now()
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
        lng = item['location']['coordinates'][0]
        lat = item['location']['coordinates'][1]
        city_slug = item['city_slug']
        
        # Create a key from name, city and approximate location
        # This is a simple approach - a production system would use better matching
        key = f"{name}_{city_slug}"
        
        # If we have lat/lng, make the key more specific
        if lat and lng:
            # Round to 3 decimal places (roughly 100m precision)
            key = f"{name}_{city_slug}_{round(float(lat), 3)}_{round(float(lng), 3)}"
        
        if key in unique_places:
            # We already have this place - merge data
            existing = unique_places[key]
            
            # Update source list
            if 'sources' not in existing:
                existing['sources'] = []
            
            for source in item.get('sources', []):
                if source not in existing['sources']:
                    existing['sources'].append(source)
            
            # Merge source IDs
            if 'source_ids' not in existing:
                existing['source_ids'] = {}
                
            for source, id_value in item.get('source_ids', {}).items():
                if id_value:  # Only add if not empty
                    existing['source_ids'][source] = id_value
            
            # Merge any missing data from the new record into the existing one
            for field, value in item.items():
                if field not in ['sources', 'source_ids'] and value and not existing.get(field):
                    existing[field] = value
        else:
            # New place
            unique_places[key] = item
    
    return list(unique_places.values())

def combine_data(city_slug=None, category=None, replace=False):
    """
    Combine data from raw_places collection and save to the processed_places collection.
    
    Args:
        city_slug (str, optional): Process only data for this city
        category (str, optional): Process only data for this category
        replace (bool): Whether to replace existing processed data
        
    Returns:
        tuple: (inserted_count, updated_count)
    """
    all_data = []
    
    # Load raw data from MongoDB
    data_by_source = load_data_from_mongodb(city_slug, category)
    
    # Normalize data from each source
    if data_by_source['yelp']:
        print(f"Normalizing {len(data_by_source['yelp'])} Yelp records...")
        normalized = normalize_yelp_data(data_by_source['yelp'])
        all_data.extend(normalized)
    
    if data_by_source['google']:
        print(f"Normalizing {len(data_by_source['google'])} Google records...")
        normalized = normalize_google_data(data_by_source['google'])
        all_data.extend(normalized)
    
    print(f"Total records before deduplication: {len(all_data)}")
    
    # Deduplicate data
    print("Deduplicating data...")
    deduplicated_data = deduplicate_data(all_data)
    
    print(f"Total records after deduplication: {len(deduplicated_data)}")
    
    # Save to MongoDB processed collection
    print(f"Saving {len(deduplicated_data)} records to MongoDB processed collection...")
    inserted, updated = save_processed_places(deduplicated_data, replace)
    print(f"Processed data saved: {inserted} new records, {updated} updated records.")
    
    return inserted, updated

def main():
    parser = argparse.ArgumentParser(description='Combine data from raw places collection')
    parser.add_argument('--replace', action='store_true',
                        help='Replace existing processed data in MongoDB')
    parser.add_argument('--city-slug', type=str, 
                        help='Process only data for this city (e.g., "seattle-wa")')
    parser.add_argument('--category', type=str,
                        help='Process only data for this category (e.g., "escapegames")')
    
    args = parser.parse_args()
    
    combine_data(args.city_slug, args.category, args.replace)

if __name__ == "__main__":
    main() 