#!/usr/bin/env python3
"""
Add a Single City to MongoDB
The simplest possible example to add a city to your database.
"""

from simple_city_fetcher import fetch_and_add_city

# Just one line to add a city
success, message, slug = fetch_and_add_city("Las Vegas", "USA")
print(message)
if success:
    print(f"City slug: {slug}")
    print(f"Use it with: python src/data_collection/yelp_collector.py --city-slug \"{slug}\" --category \"escapegames\"") 