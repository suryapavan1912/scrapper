#!/usr/bin/env python3
"""
Simple City Fetcher
Adds a city to MongoDB just using city name and country.
"""

import os
import sys
import argparse
import requests
import time
import re
from dotenv import load_dotenv
from pymongo import MongoClient, GEOSPHERE
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'mental_health_resources')
CITIES_COLLECTION = 'cities'

# Nominatim API settings
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MentalHealthResourcesWebsite/1.0"

def get_mongo_client():
    """Create and return a MongoDB client."""
    return MongoClient(MONGO_CONNECTION_STRING)

def get_database():
    """Get the MongoDB database."""
    client = get_mongo_client()
    return client[MONGO_DATABASE]

def get_cities_collection():
    """Get the cities collection."""
    db = get_database()
    return db[CITIES_COLLECTION]

def setup_collection():
    """Set up the cities collection with indexes."""
    collection = get_cities_collection()
    
    # Create indexes
    collection.create_index([("slug", 1)], unique=True)
    collection.create_index([("name", 1)])
    collection.create_index([("location", GEOSPHERE)])
    
    print("Cities collection set up with indexes.")

def fetch_and_add_city(city_name, country="USA"):
    """
    Fetch city information and add it to the database.
    
    Args:
        city_name (str): Name of the city
        country (str): Country name
        
    Returns:
        tuple: (success, message, slug)
    """
    # Fetch city info from Nominatim
    params = {
        "city": city_name,
        "country": country,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": USER_AGENT  # Required by Nominatim API
    }
    
    try:
        print(f"Fetching data for {city_name}, {country}...")
        response = requests.get(NOMINATIM_BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
        
        if not results:
            return False, f"No results found for {city_name}, {country}", None
        
        # Take the first result
        city_data = results[0]
        address = city_data.get('address', {})
        
        # Extract state information
        state_name = address.get('state')

        # Create a slug - simplified to only use city name
        slug = city_name.lower().replace(' ', '-')
        
        # Check if city already exists
        collection = get_cities_collection()
        existing = collection.find_one({"slug": slug})
        if existing:
            return False, f"City with slug '{slug}' already exists.", slug
        
        # Prepare city document
        city = {
            "name": city_name,
            "slug": slug,
            "state": state_name,
            "country": country,
            "location": {
                "type": "Point",
                "coordinates": [float(city_data.get('lon')), float(city_data.get('lat'))]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add to MongoDB
        result = collection.insert_one(city)
        return True, f"City '{city_name}, {country}' added with ID: {result.inserted_id}", slug
        
    except requests.exceptions.RequestException as e:
        return False, f"Error fetching city data: {e}", None
    except Exception as e:
        return False, f"Error adding city: {e}", None

def main():
    parser = argparse.ArgumentParser(description='Add a city to MongoDB using just name and country')
    
    # Setup command
    parser.add_argument('--setup', action='store_true', help='Set up the cities collection')
    
    # Add city command
    parser.add_argument('--city', help='City name')
    parser.add_argument('--country', default='USA', help='Country name')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_collection()
        return
    
    if not args.city:
        parser.print_help()
        return
    
    success, message, slug = fetch_and_add_city(args.city, args.country)
    print(message)
    
    if success:
        print(f"City slug: {slug}")
        print("You can now use this city with the data collectors:")
        print(f"  python src/data_collection/yelp_collector.py --city-slug \"{slug}\" --category \"escapegames\"")

if __name__ == "__main__":
    main() 