#!/usr/bin/env python3
"""
Test script for Google Places API using the new v1 endpoint
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def search_places(query, api_key):
    """
    Search for places using the Places API v1 endpoint
    """
    url = "https://places.googleapis.com/v1/places:searchText"
    
    # Headers as specified in the curl command
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.priceLevel'
    }
    
    # Request body
    data = {
        "textQuery": query
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Print the response in a formatted way
        print("\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def main():
    # Get API key from environment variables
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY not found in environment variables")
        return
    
    # Test query
    query = "top 10 rage rooms in new york city"
    print(f"\nSearching for: {query}")
    
    # Make the request
    result = search_places(query, api_key)
    
    if result:
        print("\nRequest successful!")
    else:
        print("\nRequest failed!")

if __name__ == "__main__":
    main() 