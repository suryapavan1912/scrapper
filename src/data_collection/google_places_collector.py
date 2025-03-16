#!/usr/bin/env python3
"""
Google Places API Data Collector for Mental Health Resources
This script uses the Google Places API v1 to collect data about locations
that might be relevant for mental health resources, storing all data in MongoDB.
"""

import os
import argparse
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from mongo_utils import validate_city, save_raw_places
import sys
import json

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
SEARCH_ENDPOINT = 'https://places.googleapis.com/v1/places:searchText'

# Valid place types for mental health resources
# Using hyphen format for slugs instead of underscores
VALID_PLACE_TYPES = [
    'amusement-park',
    'art-gallery',
    'bowling-alley',
    'escape-room',
    'gym',
    'spa',
    'psychologist',
    'health',
    'park',
    'museum',
    'movie-theater',
    'rage-room'
]

# Updated field mask with only valid fields for the Google Places API v1
FIELD_MASK = 'places.displayName,places.formattedAddress,places.priceLevel,places.id'

def search_places(query, page_token=None):
    """
    Search for places using Google Places API v1 Text Search.
    
    Args:
        query (str): Search query
        page_token (str, optional): Token for pagination
        
    Returns:
        dict: JSON response from Google Places API
    """
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': FIELD_MASK
    }
    
    data = {
        "textQuery": query
    }
    
    if page_token:
        data["pageToken"] = page_token
    
    try:
        response = requests.post(SEARCH_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching places: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None

def collect_data(city, place_type_slug, max_results=60):
    """
    Collect data from Google Places about places in the given location and type.
    
    Args:
        city (dict): City document from MongoDB
        place_type_slug (str): Type of place to search for (hyphenated slug)
        max_results (int): Maximum number of results to collect
        
    Returns:
        list: List of place data dictionaries
    """
    all_places = []
    
    # Construct a search query using one of the effective templates
    query = get_search_query(city, place_type_slug)
    
    page_token = None
    
    while len(all_places) < max_results:
        if page_token:
            time.sleep(2)  # Rate limiting
        
        print(f"Fetching places for '{query}'...")
        if page_token:
            print(f"Page token: {page_token[:10]}...")
        
        results = search_places(query, page_token=page_token)
        
        if not results or 'places' not in results:
            print(f"No more results found or error in API response")
            break
        
        places = results['places']
        print(f"Found {len(places)} places in this batch")
        
        # Add the category to each place as an array
        for place in places:
            place['categories'] = [place_type_slug]
        
        all_places.extend(places)
        
        # Check if there are more pages
        page_token = results.get('nextPageToken')
        if not page_token or len(all_places) >= max_results:
            break
    
    return all_places[:max_results]

def get_search_query(city, place_type_slug):
    """
    Generate an effective search query based on place type slug and location.
    
    Args:
        city (dict): City document from MongoDB
        place_type_slug (str): Type of place to search for (hyphenated slug)
        
    Returns:
        str: Formatted search query
    """
    # Get location from city document
    location = f"{city['name']}, {city['state']}"

    # Dictionary of effective query templates by place type
    query_templates = {
        'escape-room': f"top rated escape rooms in {location}",
        'rage-room': f"rage rooms in {location}",
        'health': f"mental health centers in {location}",
        'psychologist': f"top rated psychologists in {location}",
        'spa': f"best wellness spas in {location}",
        'gym': f"fitness centers in {location}",
        'park': f"relaxing parks in {location}",
        'museum': f"interactive museums in {location}",
        'movie-theater': f"movie theaters in {location}",
        'bowling-alley': f"bowling alleys in {location}",
        'art-gallery': f"interactive art galleries in {location}",
        'amusement-park': f"amusement parks in {location}",
    }
    
    # Default template if specific type not found
    default_template = f"top rated {place_type_slug.replace('-', ' ')} in {location}"
    
    # Get template for the place type or use default
    return query_templates.get(place_type_slug, default_template)

def save_data(data, city_slug, place_type_slug):
    """
    Save the collected data to MongoDB.
    
    Args:
        data (list): List of place data
        city_slug (str): City slug
        place_type_slug (str): Place type slug
        
    Returns:
        tuple: (inserted_count, updated_count)
    """
    # Save to MongoDB
    inserted_count, updated_count = save_raw_places(data, 'google', city_slug, place_type_slug)
    print(f"MongoDB: {inserted_count} new records inserted, {updated_count} records updated")
    return inserted_count, updated_count

def main():
    parser = argparse.ArgumentParser(description='Collect data from Google Places API for mental health resources')
    parser.add_argument('--city-slug', type=str, required=True, 
                        help='City slug (e.g., "seattle")')
    parser.add_argument('--type', type=str, required=True, choices=VALID_PLACE_TYPES,
                        help='Type of place to search for (with hyphens, e.g., "escape-room")')
    parser.add_argument('--max', type=int, default=60, 
                        help='Maximum number of results to collect')
    
    args = parser.parse_args()
    
    if not API_KEY:
        print("Error: Google Places API key not found. Please add it to your .env file.")
        return
    
    # Validate the city exists
    city = validate_city(args.city_slug)
    if not city:
        print(f"Error: City with slug '{args.city_slug}' not found. Please add it first using simple_city_fetcher.py.")
        sys.exit(1)
    
    print(f"Collecting data for {args.type} in {city['name']}, {city['state']}...")
    places = collect_data(city, args.type, args.max)
    
    if places:
        print(f"Found {len(places)} places. Saving to MongoDB...")
        inserted, updated = save_data(places, args.city_slug, args.type)
        
        print(f"Data collection complete! {inserted} new records, {updated} updated records.")
    else:
        print("No places found or error in API request.")

if __name__ == "__main__":
    main() 