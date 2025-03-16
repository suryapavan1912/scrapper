#!/usr/bin/env python3
"""
Combine and process data from Google Places API.
This script combines raw data from MongoDB and creates a processed dataset.
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from mongo_utils import get_database, get_collection

# Load environment variables
load_dotenv()

def load_data_from_mongodb(city_slug=None, category=None):
    """Load data from raw_places collection in MongoDB."""
    collection = get_collection('raw_places')
    
    # Build query
    query = {}
    if city_slug:
        query['city_slug'] = city_slug
    if category:
        query['category'] = category
    
    # Only get Google Places data
    query['source'] = 'google'
    
    return list(collection.find(query))

def normalize_google_data(place):
    """Normalize Google Places data to common format."""
    # Extract basic information
    name = place.get('name', '')
    address = place.get('formatted_address', '')
    phone = place.get('formatted_phone_number', '')
    website = place.get('website', '')
    rating = place.get('rating', 0.0)
    user_ratings_total = place.get('user_ratings_total', 0)
    price_level = place.get('price_level', 0)
    
    # Convert price level to $ symbols
    price_symbols = '$' * price_level if price_level else ''
    
    # Get location
    location = place.get('geometry', {}).get('location', {})
    coordinates = [location.get('lng', 0), location.get('lat', 0)]
    
    # Get opening hours
    hours = place.get('opening_hours', {}).get('weekday_text', [])
    
    # Get all types/categories
    types = place.get('types', [])
    categories = ', '.join(types)
    
    # Get photos
    photos = place.get('photos', [])
    image_url = photos[0].get('photo_reference') if photos else ''
    
    # Get additional details
    place_id = place.get('place_id', '')
    is_closed = place.get('business_status') == 'CLOSED_PERMANENTLY'
    
    return {
        "name": name,
        "address": address,
        "city_slug": place.get('city_slug', ''),
        "city_name": place.get('city_name', ''),
        "state": place.get('state', ''),
        "state_code": place.get('state_code', ''),
        "zip_code": place.get('zip_code', ''),
        "country": place.get('country', ''),
        "location": {
            "type": "Point",
            "coordinates": coordinates
        },
        "phone": phone,
        "website": website,
        "rating": rating,
        "review_count": user_ratings_total,
        "price_level": price_symbols,
        "category": types[0] if types else '',  # Primary category
        "categories": categories,
        "image_url": image_url,
        "is_closed": is_closed,
        "hours": hours,
        "source_ids": {
            "google": place_id
        },
        "sources": ["google"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

def deduplicate_data(places):
    """Remove duplicate entries based on name and location."""
    seen = set()
    unique_places = []
    
    for place in places:
        # Create a unique key based on name and coordinates
        key = (place['name'], tuple(place['location']['coordinates']))
        if key not in seen:
            seen.add(key)
            unique_places.append(place)
    
    return unique_places

def combine_data(city_slug=None, category=None, replace=False):
    """Combine data from MongoDB raw collections."""
    print("Loading raw data from MongoDB...")
    raw_data = load_data_from_mongodb(city_slug, category)
    
    if not raw_data:
        print("No raw data found in MongoDB.")
        return
    
    print(f"Processing {len(raw_data)} raw records...")
    
    # Normalize data
    normalized_data = [normalize_google_data(place) for place in raw_data]
    
    # Deduplicate
    unique_data = deduplicate_data(normalized_data)
    
    # Save to MongoDB
    collection = get_collection('processed_places')
    
    if replace:
        # Drop existing collection and create new one
        collection.drop()
        collection = get_collection('processed_places')
        print("Replaced existing processed data.")
    
    # Insert new data
    if unique_data:
        result = collection.insert_many(unique_data)
        print(f"Added {len(result.inserted_ids)} processed records to MongoDB.")
    else:
        print("No unique records to add.")

def main():
    parser = argparse.ArgumentParser(description='Combine and process data from Google Places API')
    parser.add_argument('--city-slug', help='Process data for a specific city')
    parser.add_argument('--category', help='Process data for a specific category')
    parser.add_argument('--replace', action='store_true', help='Replace existing processed data')
    
    args = parser.parse_args()
    
    combine_data(args.city_slug, args.category, args.replace)

if __name__ == "__main__":
    main() 