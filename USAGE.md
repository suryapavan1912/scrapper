# Mental Health Resources Data Collector - Usage Guide

This guide provides step-by-step instructions for collecting data about mental health resources using the Yelp Fusion API (free tier) and Google Places API (with free credits), storing all data in MongoDB.

## Prerequisites

1. Create accounts and obtain API keys:
   - [Yelp Fusion API](https://docs.developer.yelp.com/page/start-your-free-trial) - Free tier with 500 calls/day
   - [Google Cloud Platform](https://developers.google.com/maps/documentation/places/web-service/get-api-key) - $200 free monthly credits

2. Install MongoDB:
   - [MongoDB Community Edition](https://www.mongodb.com/try/download/community) - Free, open-source database
   - Alternatively, you can use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Cloud-hosted MongoDB with a free tier

3. Set up your environment:
   ```bash
   # Clone the repository (if you haven't already)
   git clone <repository-url>
   cd <repository-directory>
   
   # Install required dependencies
   pip install -r requirements.txt
   
   # Create .env file with your API keys and MongoDB connection string
   cp .env.example .env
   # Edit the .env file to add your actual API keys and MongoDB details
   ```

## MongoDB Configuration

The system uses MongoDB to store city information, raw API data, and processed data. Configure your MongoDB connection in the `.env` file:

```
# MongoDB Connection
MONGO_CONNECTION_STRING=mongodb://localhost:27017/
MONGO_DATABASE=mental_health_resources
```

- For a local MongoDB installation, use `mongodb://localhost:27017/`
- For MongoDB Atlas, use the connection string provided in your Atlas dashboard
- You can customize the database name as needed

## Step 1: Set Up Cities

Before collecting data, you need to add city information to the database:

```bash
# First, set up the cities collection (only needed once)
python src/data_collection/simple_city_fetcher.py --setup

# Add a city to the database
python src/data_collection/simple_city_fetcher.py --city "Seattle" --country "USA"
```

For convenience, there are also two additional scripts:

```bash
# Add a single city with one line
python src/data_collection/add_city.py
# This example adds Las Vegas, USA

# Add multiple cities at once
python src/data_collection/add_cities.py
# This adds a pre-defined list of popular cities
```

The city fetcher automatically:
1. Finds the city coordinates using the Nominatim API (OpenStreetMap)
2. Determines state/province information
3. Creates the proper city slug (e.g., "seattle-wa")
4. Adds the complete city record to MongoDB

Each city needs to be added only once. After adding cities, you can proceed to collect data.

## Step 2: Collect Data from Yelp API

The Yelp API is completely free (up to 500 calls/day) and provides rich data about businesses:

```bash
# Basic usage - search for escape rooms in Seattle
python src/data_collection/yelp_collector.py --city-slug "seattle-wa" --category "escapegames"

# Collect data about meditation centers in Portland
python src/data_collection/yelp_collector.py --city-slug "portland-or" --category "meditationcenters"

# Limit results to 20 items
python src/data_collection/yelp_collector.py --city-slug "new-york-ny" --category "therapists" --max 20
```

Available categories for Yelp:
- `escapegames` - Escape rooms
- `arcades` - Arcade games
- `meditationcenters` - Meditation centers
- `yoga` - Yoga studios
- `psychologists` - Psychologist offices
- `therapists` - Therapist offices
- `martialarts` - Martial arts studios
- `boxing` - Boxing gyms
- `parks` - Parks
- `museums` - Museums
- `artclasses` - Art classes

## Step 3: Collect Data from Google Places API

Google Places API offers broader data but uses credits. The first $200 of usage each month is free:

```bash
# Basic usage - search for escape rooms in Seattle
python src/data_collection/google_places_collector.py --city-slug "seattle-wa" --type "escape_room"

# Collect data about museums in Portland
python src/data_collection/google_places_collector.py --city-slug "portland-or" --type "museum"

# Limit results to 20 items
python src/data_collection/google_places_collector.py --city-slug "new-york-ny" --type "spa" --max 20
```

Available place types for Google:
- `amusement_park` - Amusement parks
- `art_gallery` - Art galleries
- `bowling_alley` - Bowling alleys
- `escape_room` - Escape rooms
- `gym` - Fitness centers
- `spa` - Spas and wellness centers
- `psychologist` - Psychologist offices
- `health` - Health facilities
- `park` - Parks
- `museum` - Museums
- `movie_theater` - Movie theaters

## Step 4: Process and Combine Data

After collecting raw data from both APIs into MongoDB, you can process it to create a cleaned, deduplicated dataset:

```bash
# Basic usage - combine all data from MongoDB raw collections
python src/data_collection/combine_data.py

# Process data for a specific city
python src/data_collection/combine_data.py --city-slug "seattle-wa"

# Process data for a specific category
python src/data_collection/combine_data.py --category "escapegames"

# Replace existing processed data (instead of updating)
python src/data_collection/combine_data.py --replace
```

This will:
1. Load raw data from the raw_places collection
2. Normalize the data to a common format
3. Deduplicate entries that appear in both datasets
4. Save the processed data to the processed_places collection

## MongoDB Collections Structure

The MongoDB database is organized with three main collections:

- **Cities Collection** (`cities`)
  - Contains information about cities, including name, slug, state, coordinates
  - Each city has a unique slug (e.g., "seattle-wa")
  - Used to validate data collection requests
  - Stores geographical information for website city pages

- **Raw Places Collection** (`raw_places`)
  - Contains the original, unmodified data from the APIs
  - Each document includes metadata about the source, city, and category
  - When importing new data, existing entries are updated
  - Best for inspecting raw API responses

- **Processed Places Collection** (`processed_places`)
  - Contains normalized, deduplicated data
  - All data follows a consistent schema regardless of source
  - Includes source IDs to trace back to original data
  - Ready to use in your website

## Accessing the Data for Your Website

To use the processed data in your website, connect to the MongoDB database and query the processed collection:

```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mental_health_resources']
collection = db['processed_places']

# Example: Get all places in a specific city
city_places = collection.find({'city_slug': 'seattle-wa'})

# Example: Get places by category
escape_rooms = collection.find({'category': 'escapegames'})

# Example: Get places by rating (4.5 stars or higher)
top_rated = collection.find({'rating': {'$gte': 4.5}})

# Example: Get cities
cities_collection = db['cities']
all_cities = list(cities_collection.find({}))
```

## Data Schema

### Cities Collection Schema
```
{
  "_id": ObjectId,            // MongoDB document ID
  "name": String,             // City name (e.g. "Seattle")
  "slug": String,             // URL-friendly identifier (e.g. "seattle-wa")
  "state": String,            // State name (e.g. "Washington")
  "state_code": String,       // State code (e.g. "WA")
  "country": String,          // Country (default "USA")
  "location": {               // GeoJSON Point
    "type": "Point",
    "coordinates": [Number, Number]  // [longitude, latitude]
  },
  "population": Number,       // Optional population count
  "timezone": String,         // Optional timezone
  "created_at": Date,         // Creation timestamp
  "updated_at": Date          // Last updated timestamp
}
```

### Raw Places Collection Schema
The raw schema varies by source (Yelp or Google) but includes these common fields:
```
{
  "_id": ObjectId,            // MongoDB document ID
  "source": String,           // 'yelp' or 'google'
  "city_slug": String,        // City slug (e.g. "seattle-wa")
  "city_name": String,        // City name
  "city_id": ObjectId,        // Reference to city document
  "state": String,            // State name
  "state_code": String,       // State code
  "category": String,         // Category used for collection
  "yelp_id": String,          // Yelp Business ID (for Yelp data)
  "google_id": String,        // Google Place ID (for Google data)
  "updated_at": Date,         // Last updated timestamp
  ... additional API-specific fields ...
}
```

### Processed Places Collection Schema
```
{
  "_id": ObjectId,            // MongoDB document ID
  "name": String,             // Business/place name
  "address": String,          // Formatted address
  "city_slug": String,        // City slug (e.g. "seattle-wa")
  "city_name": String,        // City name
  "state": String,            // State name
  "state_code": String,       // State code
  "zip_code": String,         // Postal code
  "country": String,          // Country 
  "location": {               // GeoJSON Point
    "type": "Point",
    "coordinates": [Number, Number]  // [longitude, latitude]
  },
  "phone": String,            // Formatted phone number
  "website": String,          // Website URL
  "rating": Number,           // Numerical rating (typically 1-5)
  "review_count": Number,     // Number of reviews
  "price_level": String,      // Price level as $ symbols
  "category": String,         // Primary category 
  "categories": String,       // Comma-separated categories/types
  "image_url": String,        // Main image URL
  "is_closed": Boolean,       // Whether the place is permanently closed
  "hours": Array,             // Opening hours information
  "source_ids": {             // Original IDs from each source
    "yelp": String,
    "google": String
  },
  "sources": Array,           // List of data sources ['yelp', 'google']
  "created_at": Date,         // Creation timestamp
  "updated_at": Date          // Last updated timestamp
}
```

## Tips for Efficient API and MongoDB Usage

### Yelp API (Free Tier - 500 calls/day)
- Each city+category search counts as one API call
- Getting detailed business information counts as additional calls
- Plan searches to stay within the daily limit
- Script automatically respects rate limits

### Google Places API (Free Credits - $200/month)
- Text searches cost about $0.04 per request (10,000 searches = $400)
- Place details cost about $0.006 per request (40,000 detail lookups = $240)
- The free $200 credit should allow for roughly 2,000-3,000 places per month
- Script automatically respects rate limits
- Our script fetches ALL available fields in the API response

### MongoDB Usage
- The system now uses a single raw_places collection for all data
- When collecting new data, existing entries are updated rather than duplicated
- The processed_places collection contains deduplicated data from all sources
- For production, set up MongoDB authentication
- Consider setting up MongoDB Atlas for cloud-hosted access from your website

## Troubleshooting

**API Key Issues:**
- Ensure your API keys are correctly entered in the `.env` file
- For Google, make sure you've enabled the Places API in your Google Cloud Console

**MongoDB Connection Issues:**
- Check your MongoDB connection string in the `.env` file
- Ensure MongoDB is running on your system or Atlas is configured correctly
- Try connecting to MongoDB using the MongoDB shell or MongoDB Compass

**City Not Found:**
- Make sure you've added the city using the simple_city_fetcher.py script
- Check the city slug format (typically "cityname-statecode" in lowercase)
- Run `python src/data_collection/simple_city_fetcher.py --city "New York" --country "USA"` to add cities

**No Results Found:**
- Try different category/type terms
- Ensure the location is valid
- Try a larger, more well-known city first

**Rate Limiting:**
- If you hit rate limits, the script will automatically slow down
- For persistent issues, reduce the `--max` parameter 

## City Data Fetcher: Automatic City Information Retrieval

The Simple City Fetcher utility adds city information to your database when you only have the city name and country. This utility automates the entire process of:

1. Finding city coordinates
2. Determining state/province information
3. Creating proper city slugs
4. Adding complete city records to your MongoDB

### Key Features

- **Minimal Information Required**: Just provide city name and country
- **Uses Free OpenStreetMap API**: No API keys or costs required
- **Command Line Interface**: Simple and straightforward usage

### How It Works

The utility uses the Nominatim API from OpenStreetMap to geocode city names, retrieve location details, and extract state/province information. For US cities, it maps state names to their two-letter codes, creating properly formatted city slugs.

### Usage Examples

Here are ways to use the utility:

```bash
# Set up the collection (only needed once)
python src/data_collection/simple_city_fetcher.py --setup

# Add a city to database
python src/data_collection/simple_city_fetcher.py --city "Toronto" --country "Canada"
```

You can also use the provided helper scripts:

```bash
# Add a single city (Las Vegas, USA) with one line
python src/data_collection/add_city.py

# Add multiple popular cities at once
python src/data_collection/add_cities.py
```

### Integration with Your Collectors

Once cities are in your database, you can use them with your data collectors:

```bash
# Use the city slugs with your collectors
python src/data_collection/yelp_collector.py --city-slug "toronto-on" --category "escapegames"
```

This utility makes setting up and maintaining your city database entirely painless. You can now focus on collecting venue data rather than manually researching city details.

from simple_city_fetcher import fetch_and_add_city

# That's it - just one line!
success, message, slug = fetch_and_add_city("Las Vegas", "USA") 