#!/usr/bin/env python3
"""
Google Places API Data Collector for Mental Health Resources
This script uses the Google Places API to collect data about locations
that might be relevant for mental health resources.
"""

import os
import json
import argparse
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
BASE_URL = 'https://maps.googleapis.com/maps/api/place'
SEARCH_ENDPOINT = f'{BASE_URL}/textsearch/json'
DETAILS_ENDPOINT = f'{BASE_URL}/details/json'
DEFAULT_LOCATION = 'Seattle, WA'

# Valid place types for mental health resources
VALID_PLACE_TYPES = [
    'amusement_park',
    'art_gallery',
    'bowling_alley',
    'escape_room',  # Note: This might return fewer results as it's not a standard Google type
    'gym',
    'spa',
    'psychologist',
    'health',
    'park',
    'museum',
    'movie_theater'
]

def search_places(query, place_type=None, page_token=None):
    """
    Search for places using Google Places API Text Search.
    
    Args:
        query (str): Search query (e.g., "city name + place type")
        place_type (str, optional): Type of place to search for
        page_token (str, optional): Token for pagination
        
    Returns:
        dict: JSON response from Google Places API
    """
    params = {
        'query': query,
        'key': API_KEY
    }
    
    if place_type:
        params['type'] = place_type
        
    if page_token:
        params['pagetoken'] = page_token
    
    try:
        response = requests.get(SEARCH_ENDPOINT, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching places: {e}")
        return None

def get_place_details(place_id):
    """
    Get detailed information about a specific place.
    
    Args:
        place_id (str): Google Places place ID
        
    Returns:
        dict: JSON response with place details
    """
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,price_level,opening_hours,geometry,photos,reviews',
        'key': API_KEY
    }
    
    try:
        response = requests.get(DETAILS_ENDPOINT, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting place details: {e}")
        return None

def collect_data(location, place_type, max_results=60):
    """
    Collect data from Google Places about places in the given location and type.
    
    Args:
        location (str): City name or location
        place_type (str): Type of place to search for
        max_results (int): Maximum number of results to collect
        
    Returns:
        list: List of place data dictionaries
    """
    all_places = []
    query = f"{place_type} in {location}"
    page_token = None
    
    # Google Places API usually returns 20 results per page
    # and allows up to 3 pages (60 results total) per query
    
    while len(all_places) < max_results:
        if page_token:
            # Google requires a delay before using a page token
            time.sleep(2)
            
        print(f"Fetching places for '{query}'...")
        if page_token:
            print(f"Page token: {page_token[:10]}...")
            
        results = search_places(query, place_type, page_token)
        
        if not results or results.get('status') != 'OK' or 'results' not in results:
            print(f"No more results found or error in API response: {results.get('status', 'Unknown error')}")
            if results and 'error_message' in results:
                print(f"Error message: {results['error_message']}")
            break
            
        places = results['results']
        all_places.extend(places)
        
        # Check if there are more pages
        page_token = results.get('next_page_token')
        if not page_token or len(all_places) >= max_results:
            break
    
    # Truncate to max_results if we went over
    return all_places[:max_results]

def enrich_data(places):
    """
    Enrich place data with additional details from the details endpoint.
    
    Args:
        places (list): List of place data dictionaries
        
    Returns:
        list: Enriched place data
    """
    enriched_places = []
    
    for i, place in enumerate(places):
        print(f"Enriching data for place {i+1}/{len(places)}: {place['name']}")
        
        # Get additional details
        details_response = get_place_details(place['place_id'])
        
        if details_response and details_response.get('status') == 'OK' and 'result' in details_response:
            details = details_response['result']
            
            # Create a new dict with both original data and detailed data
            enriched_place = {
                **place,
                'website': details.get('website', ''),
                'formatted_phone_number': details.get('formatted_phone_number', ''),
                'opening_hours': details.get('opening_hours', {}),
                'reviews': details.get('reviews', [])
            }
            enriched_places.append(enriched_place)
        else:
            # If details request failed, just use the original data
            enriched_places.append(place)
        
        # Add a small delay to avoid hitting API rate limits
        time.sleep(0.2)
    
    return enriched_places

def save_data(data, location, place_type):
    """
    Save the collected data to JSON and CSV files.
    
    Args:
        data (list): List of place data
        location (str): Location name
        place_type (str): Place type
    """
    # Create sanitized filenames
    location_sanitized = location.replace(',', '').replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save as JSON
    json_filename = f"data/google_{location_sanitized}_{place_type}_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Convert to DataFrame and save as CSV
    try:
        # Flatten the data for CSV (take only top-level fields)
        flattened_data = []
        for place in data:
            flat_place = {
                'place_id': place.get('place_id', ''),
                'name': place.get('name', ''),
                'address': place.get('formatted_address', ''),
                'phone': place.get('formatted_phone_number', ''),
                'website': place.get('website', ''),
                'rating': place.get('rating', ''),
                'user_ratings_total': place.get('user_ratings_total', ''),
                'price_level': place.get('price_level', ''),
                'latitude': place.get('geometry', {}).get('location', {}).get('lat', ''),
                'longitude': place.get('geometry', {}).get('location', {}).get('lng', ''),
                'types': ', '.join(place.get('types', [])),
                'business_status': place.get('business_status', '')
            }
            flattened_data.append(flat_place)
        
        df = pd.DataFrame(flattened_data)
        csv_filename = f"data/google_{location_sanitized}_{place_type}_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        
        print(f"Data saved to {json_filename} and {csv_filename}")
    except Exception as e:
        print(f"Error saving CSV: {e}")
        print(f"Data saved to {json_filename}")

def main():
    parser = argparse.ArgumentParser(description='Collect data from Google Places API for mental health resources')
    parser.add_argument('--city', type=str, default=DEFAULT_LOCATION, 
                        help='City name (e.g., "Seattle, WA")')
    parser.add_argument('--type', type=str, required=True, choices=VALID_PLACE_TYPES,
                        help='Type of place to search for')
    parser.add_argument('--max', type=int, default=60, 
                        help='Maximum number of results to collect')
    
    args = parser.parse_args()
    
    if not API_KEY:
        print("Error: Google Places API key not found. Please add it to your .env file.")
        return
    
    print(f"Collecting data for {args.type} in {args.city}...")
    places = collect_data(args.city, args.type, args.max)
    
    if places:
        print(f"Found {len(places)} places. Enriching data...")
        enriched_places = enrich_data(places)
        
        print(f"Saving data for {len(enriched_places)} places...")
        save_data(enriched_places, args.city, args.type)
        
        print("Data collection complete!")
    else:
        print("No places found or error in API request.")

if __name__ == "__main__":
    main() 