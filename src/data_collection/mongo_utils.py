#!/usr/bin/env python3
"""
MongoDB utilities for mental health resources data collection.
This module provides shared database functions for the data collection system.
"""

import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'mental_health_resources')

# Collection names
CITIES_COLLECTION = 'cities'
RAW_PLACES_COLLECTION = 'raw_places'
PROCESSED_PLACES_COLLECTION = 'processed_places'

def get_mongo_client():
    """Create and return a MongoDB client."""
    return MongoClient(MONGO_CONNECTION_STRING)

def get_database():
    """Get the MongoDB database."""
    client = get_mongo_client()
    return client[MONGO_DATABASE]

def get_collection(collection_name):
    """Get a MongoDB collection by name."""
    db = get_database()
    return db[collection_name]

def get_cities_collection():
    """Get the cities collection."""
    return get_collection(CITIES_COLLECTION)

def get_raw_places_collection():
    """Get the raw places collection."""
    return get_collection(RAW_PLACES_COLLECTION)

def get_processed_places_collection():
    """Get the processed places collection."""
    return get_collection(PROCESSED_PLACES_COLLECTION)

def validate_city(city_slug):
    """
    Validate that a city exists in the database.
    
    Args:
        city_slug (str): The city slug to validate.
        
    Returns:
        dict: The city document if found, None otherwise.
    """
    cities_collection = get_cities_collection()
    return cities_collection.find_one({"slug": city_slug})

def save_raw_places(places, source, city_slug, category):
    """
    Save raw place data to MongoDB, updating existing entries if they exist.
    If a place with the same ID already exists, add the new category to its categories.
    
    Args:
        places (list): List of place dictionaries.
        source (str): The data source (always 'google').
        city_slug (str): The city slug.
        category (str): The category of places.
        
    Returns:
        tuple: (inserted_count, updated_count)
    """
    # Get city information
    city = validate_city(city_slug)
    if not city:
        raise ValueError(f"City with slug '{city_slug}' not found. Please add it first.")
    
    collection = get_raw_places_collection()
    
    # Set up indexes if they don't exist
    collection.create_index([("source", 1)])
    collection.create_index([("city_slug", 1)])
    collection.create_index([("categories", 1)])
    collection.create_index([("id", 1)], sparse=True)
    
    inserted_count = 0
    updated_count = 0
    
    for place in places:
        # Add metadata
        place['source'] = source
        place['city_slug'] = city_slug
        place['city_id'] = city['_id']
        place['city_name'] = city['name']
        place['state'] = city['state']
        place['state_code'] = city['state_code']
        
        # Ensure place has a categories array with the current category
        if 'categories' not in place:
            place['categories'] = [category]
            
        place['updated_at'] = datetime.now()
        
        # Define the query to find existing place
        query = {'source': 'google', 'id': place['id']}
        
        # Check if the place already exists
        existing_place = collection.find_one(query)
        
        if existing_place:
            # Place exists, update it and append the category if not already present
            existing_categories = existing_place.get('categories', [])
            
            # Add the new category if it's not already in the list
            if category not in existing_categories:
                existing_categories.append(category)
            
            # Update the place with merged categories
            place['categories'] = existing_categories
            
            # Update the document
            result = collection.update_one(query, {'$set': place})
            updated_count += 1
        else:
            # Place doesn't exist, insert it
            result = collection.insert_one(place)
            inserted_count += 1
    
    return inserted_count, updated_count

def get_raw_places(city_slug=None, category=None):
    """
    Get raw places data from MongoDB with optional filtering.
    
    Args:
        city_slug (str, optional): Filter by city slug.
        category (str, optional): Filter by category.
        
    Returns:
        list: List of place dictionaries.
    """
    collection = get_raw_places_collection()
    
    query = {'source': 'google'}
    if city_slug:
        query['city_slug'] = city_slug
    if category:
        # Filter by category in the categories array
        query['categories'] = category
    
    return list(collection.find(query))

def save_processed_places(places, replace=False):
    """
    Save processed place data to MongoDB.
    
    Args:
        places (list): List of processed place dictionaries.
        replace (bool): Whether to replace the existing collection.
        
    Returns:
        tuple: (inserted_count, updated_count)
    """
    collection = get_processed_places_collection()
    
    # Set up indexes if they don't exist
    collection.create_index([("city_slug", 1)])
    collection.create_index([("categories", 1)])
    collection.create_index([("source_id", 1)], sparse=True)
    collection.create_index([("location", "2dsphere")])
    
    # If replace flag is set, drop the collection first
    if replace:
        collection.drop()
        # Recreate indexes
        collection.create_index([("city_slug", 1)])
        collection.create_index([("categories", 1)])
        collection.create_index([("source_id", 1)], sparse=True)
        collection.create_index([("location", "2dsphere")])
    
    inserted_count = 0
    updated_count = 0
    
    for place in places:
        # Add updated timestamp
        place['updated_at'] = datetime.now()
        
        # Build query to find existing place
        query = {}
        if 'source_id' in place and place['source_id']:
            query = {"source_id": place['source_id']}
        
        if not query and 'city_slug' in place and 'name' in place:
            # If no source ID, try to match by name and city
            query = {
                "city_slug": place['city_slug'],
                "name": place['name']
            }
        
        if not query:
            # If no query can be built, just insert
            result = collection.insert_one(place)
            inserted_count += 1
            continue
        
        # Check if document exists to handle categories properly
        existing_place = collection.find_one(query)
        if existing_place and 'categories' in place and 'categories' in existing_place:
            # Merge categories from existing and new place
            all_categories = set(existing_place['categories'])
            all_categories.update(place['categories'])
            place['categories'] = list(all_categories)
        
        # Update or insert the document
        result = collection.update_one(
            query,
            {'$set': place},
            upsert=True
        )
        
        if result.matched_count > 0:
            updated_count += 1
        else:
            inserted_count += 1
    
    return inserted_count, updated_count

def get_processed_places(city_slug=None, category=None):
    """
    Get processed places data from MongoDB with optional filtering.
    
    Args:
        city_slug (str, optional): Filter by city slug.
        category (str, optional): Filter by category.
        
    Returns:
        list: List of place dictionaries.
    """
    collection = get_processed_places_collection()
    
    query = {}
    if city_slug:
        query['city_slug'] = city_slug
    if category:
        # Updated to search in the categories array
        query['categories'] = category
    
    return list(collection.find(query)) 