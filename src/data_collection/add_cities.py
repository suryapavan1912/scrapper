#!/usr/bin/env python3
"""
Add Cities to MongoDB
Simple script to add multiple cities to your database using just name and country.
"""

from simple_city_fetcher import fetch_and_add_city, setup_collection
import time

def add_cities():
    """Add a list of cities to MongoDB."""
    # First make sure the collection is set up with proper indexes
    setup_collection()
    
    # List of cities to add
    cities_to_add = [
        # Format: (city_name, country)
        ("New York", "USA"),
        ("Los Angeles", "USA"),
        ("Chicago", "USA"),
        ("San Francisco", "USA"),
        ("Miami", "USA"),
        ("London", "UK"),
        ("Paris", "France"),
        ("Berlin", "Germany"),
        ("Tokyo", "Japan"),
        ("Sydney", "Australia"),
    ]
    
    added_count = 0
    
    for city_name, country in cities_to_add:
        print(f"\nAdding {city_name}, {country}...")
        success, message, slug = fetch_and_add_city(city_name, country)
        print(message)
        
        if success:
            print(f"City slug: {slug}")
            added_count += 1
        
        # Respect Nominatim usage policy - max 1 request per second
        time.sleep(1)
    
    print(f"\nAdded {added_count} out of {len(cities_to_add)} cities.")
    print("You can now use these cities with your data collectors.")

if __name__ == "__main__":
    add_cities() 