#!/usr/bin/env python3
"""
Yelp Fusion API Data Collector for Mental Health Resources
This script uses the free tier of Yelp's Fusion API to collect data about locations
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

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('YELP_API_KEY')
BASE_URL = 'https://api.yelp.com/v3'
SEARCH_ENDPOINT = f'{BASE_URL}/businesses/search'
BUSINESS_ENDPOINT = f'{BASE_URL}/businesses/'
DEFAULT_LOCATION = 'Seattle, WA'

# Valid categories for mental health resources
VALID_CATEGORIES = [
    'escapegames',
    'arcades',
    'meditationcenters',
    'yoga',
    'psychologists',
    'therapists',
    'martialarts',
    'boxing',
    'parks',
    'museums',
    'artclasses'
]

def get_headers():
    """Return the headers needed for Yelp API requests."""
    return {
        'Authorization': f'Bearer {API_KEY}'
    }

def search_businesses(location, category, limit=50, offset=0):
    """
    Search for businesses by location and category.
    
    Args:
        location (str): City name or location
        category (str): Business category to search for
        limit (int): Number of results to return (max 50)
        offset (int): Offset for pagination
        
    Returns:
        dict: JSON response from Yelp API
    """
    params = {
        'location': location,
        'categories': category,
        'limit': limit,
        'offset': offset,
        'sort_by': 'best_match'
    }
    
    try:
        response = requests.get(SEARCH_ENDPOINT, headers=get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching businesses: {e}")
        return None

def get_business_details(business_id):
    """
    Get detailed information about a specific business.
    Getting all fields by not specifying the fields parameter.
    
    Args:
        business_id (str): Yelp business ID
        
    Returns:
        dict: JSON response with business details
    """
    url = f"{BUSINESS_ENDPOINT}{business_id}"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting business details: {e}")
        return None

def collect_data(location, category, max_results=100):
    """
    Collect data from Yelp about businesses in the given location and category.
    
    Args:
        location (str): City name or location
        category (str): Business category to search for
        max_results (int): Maximum number of results to collect
        
    Returns:
        list: List of business data dictionaries
    """
    all_businesses = []
    offset = 0
    limit = min(50, max_results)  # Yelp limits to 50 per request
    
    while len(all_businesses) < max_results:
        print(f"Fetching results {offset+1} to {offset+limit} for {category} in {location}...")
        
        results = search_businesses(location, category, limit, offset)
        
        if not results or 'businesses' not in results or not results['businesses']:
            print("No more results found or error in API response.")
            break
            
        businesses = results['businesses']
        all_businesses.extend(businesses)
        
        if len(businesses) < limit:
            # We've reached the end of the results
            break
            
        offset += limit
        limit = min(50, max_results - len(all_businesses))
        
        # Respect Yelp API rate limits (max 5 requests per second)
        time.sleep(0.2)
    
    # Truncate to max_results if we went over
    return all_businesses[:max_results]

def enrich_data(businesses):
    """
    Enrich business data with additional details from the business endpoint.
    
    Args:
        businesses (list): List of business data dictionaries
        
    Returns:
        list: Enriched business data
    """
    enriched_businesses = []
    
    for i, business in enumerate(businesses):
        print(f"Enriching data for business {i+1}/{len(businesses)}: {business['name']}")
        
        # Get additional details
        details = get_business_details(business['id'])
        
        if details:
            # Merge the original data with the detailed data
            enriched_business = {**business, **details}
            enriched_businesses.append(enriched_business)
        else:
            # If details request failed, just use the original data
            enriched_businesses.append(business)
        
        # Respect Yelp API rate limits
        time.sleep(0.2)
    
    return enriched_businesses

def save_data(data, city_slug, category):
    """
    Save the collected data to MongoDB.
    
    Args:
        data (list): List of business data
        city_slug (str): City slug
        category (str): Category name
        
    Returns:
        tuple: (inserted_count, updated_count)
    """
    # Save to MongoDB
    inserted_count, updated_count = save_raw_places(data, 'yelp', city_slug, category)
    print(f"MongoDB: {inserted_count} new records inserted, {updated_count} records updated")
    return inserted_count, updated_count

def main():
    parser = argparse.ArgumentParser(description='Collect data from Yelp API for mental health resources')
    parser.add_argument('--city-slug', type=str, required=True, 
                        help='City slug (e.g., "seattle-wa")')
    parser.add_argument('--category', type=str, required=True, choices=VALID_CATEGORIES,
                        help='Category to search for')
    parser.add_argument('--max', type=int, default=100, 
                        help='Maximum number of results to collect')
    
    args = parser.parse_args()
    
    if not API_KEY:
        print("Error: Yelp API key not found. Please add it to your .env file.")
        return
    
    # Validate the city exists
    city = validate_city(args.city_slug)
    if not city:
        print(f"Error: City with slug '{args.city_slug}' not found. Please add it first using simple_city_fetcher.py.")
        sys.exit(1)
    
    print(f"Collecting data for {args.category} in {city['name']}, {city['state_code']}...")
    location = f"{city['name']}, {city['state_code']}"
    businesses = collect_data(location, args.category, args.max)
    
    if businesses:
        print(f"Found {len(businesses)} businesses. Enriching data...")
        enriched_businesses = enrich_data(businesses)
        
        print(f"Saving {len(enriched_businesses)} businesses to MongoDB...")
        inserted, updated = save_data(enriched_businesses, args.city_slug, args.category)
        
        print(f"Data collection complete! {inserted} new records, {updated} updated records.")
    else:
        print("No businesses found or error in API request.")

if __name__ == "__main__":
    main() 