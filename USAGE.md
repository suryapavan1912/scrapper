# Mental Health Resources Data Collector - Usage Guide

This guide provides step-by-step instructions for collecting data about mental health resources using the Google Places API (with free credits), storing all data in MongoDB.

## Prerequisites

1. Create a Google Cloud Platform account and obtain API key:
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
   
   # Create .env file with your API key and MongoDB connection string
   cp .env.example .env
   # Edit the .env file to add your actual API key and MongoDB details
   ```

## MongoDB Configuration

The system uses MongoDB to store city information, raw API data, and processed data. Configure your MongoDB connection in the `.env` file:

```
# MongoDB Connection
MONGO_CONNECTION_STRING=mongodb://localhost:27017/
MONGO_DATABASE=mental_health_resources

# Google Places API
GOOGLE_PLACES_API_KEY=your_api_key_here
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
3. Creates the proper city slug (e.g., "seattle")
4. Adds the complete city record to MongoDB

Each city needs to be added only once. After adding cities, you can proceed to collect data.

## Step 2: Collect Data from Google Places API

Google Places API offers comprehensive data about places. The first $200 of usage each month is free:

```bash
# Basic usage - search for escape rooms in Seattle
python src/data_collection/google_places_collector.py --city-slug "seattle" --type "escape-room"

# Collect data about museums in Portland
python src/data_collection/google_places_collector.py --city-slug "portland" --type "museum"

# Limit results to 20 items
python src/data_collection/google_places_collector.py --city-slug "new-york" --type "spa" --max 20
```

Available place types for Google:
- `amusement-park` - Amusement parks
- `art-gallery` - Art galleries
- `bowling-alley` - Bowling alleys
- `escape-room` - Escape rooms
- `gym` - Fitness centers
- `spa` - Spas and wellness centers
- `psychologist` - Psychologist offices
- `health` - Health facilities
- `park` - Parks
- `museum` - Museums
- `movie-theater` - Movie theaters
- `rage-room` - Rage rooms

### Optimized Search Queries

The collector uses optimized search query templates for each place type to get the best results:

| Place Type | Example Query Templates |
|------------|-------------------------|
| escape-room | "top rated escape rooms in [city]" |
| rage-room | "rage rooms in [city]" |
| health | "mental health centers in [city]" |
| psychologist | "top rated psychologists in [city]" |
| spa | "best wellness spas in [city]" |
| gym | "fitness centers in [city]" |
| park | "relaxing parks in [city]" |
| museum | "interactive museums in [city]" |
| movie-theater | "movie theaters in [city]" |
| bowling-alley | "bowling alleys in [city]" |
| art-gallery | "interactive art galleries in [city]" |
| amusement-park | "amusement parks in [city]" |

These templates are designed to yield the most relevant results for each category. The collector automatically selects the appropriate template based on the place type.

### Category Storage

Each place record in the database now includes a `category` field that indicates which category it was collected under. This makes it easier to filter and organize the data later.

### How the Collector Works

1. The script validates that the city exists in the database
2. It constructs an optimized search query based on the place type
3. It uses the city's coordinates for location-based search
4. It collects data using the Google Places API v1 Text Search endpoint
5. It adds the category to each place record
6. All data is saved directly to MongoDB without requiring a separate details API call
7. Pagination is handled automatically to collect up to the specified maximum number of results

### Field Mask

The collector requests a comprehensive set of fields from the API in a single request:
- Basic information (name, address, type)
- Contact details (phone, website)
- Ratings and reviews
- Opening hours
- Location coordinates
- Photos
- Editorial summaries

This eliminates the need for separate API calls to get place details.

## Step 3: Process and Combine Data

After collecting raw data from Google Places API into MongoDB, you can process it to create a cleaned, deduplicated dataset:

```bash
# Basic usage - combine all data from MongoDB raw collections
python src/data_collection/combine_data.py

# Process data for a specific city
python src/data_collection/combine_data.py --city-slug "seattle"

# Process data for a specific category
python src/data_collection/combine_data.py --category "escape_room"

# Replace existing processed data (instead of updating)
python src/data_collection/combine_data.py --replace
```

This will:
1. Load raw data from the raw_places collection
2. Normalize the data to a common format
3. Deduplicate entries
4. Save the processed data to the processed_places collection

## MongoDB Collections Structure

The MongoDB database is organized with three main collections:

- **Cities Collection** (`cities`)
  - Contains information about cities, including name, slug, state, coordinates
  - Each city has a unique slug (e.g., "seattle")
  - Used to validate data collection requests
  - Stores geographical information for website city pages

- **Raw Places Collection** (`raw_places`)
  - Contains the original, unmodified data from Google Places API
  - Each document includes metadata about the city and category
  - When importing new data, existing entries are updated
  - Best for inspecting raw API responses

- **Processed Places Collection** (`processed_places`)
  - Contains normalized, deduplicated data
  - All data follows a consistent schema
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
city_places = collection.find({'city_slug': 'seattle'})

# Example: Get places by category
escape_rooms = collection.find({'category': 'escape_room'})

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
  "slug": String,             // URL-friendly identifier (e.g. "seattle")
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
The raw schema includes these fields:
```
{
  "_id": ObjectId,            // MongoDB document ID
  "source": String,           // Always 'google'
  "city_slug": String,        // City slug (e.g. "seattle")
  "city_name": String,        // City name
  "city_id": ObjectId,        // Reference to city document
  "state": String,            // State name
  "state_code": String,       // State code
  "category": String,         // Category used for collection
  "google_id": String,        // Google Place ID
  "updated_at": Date,         // Last updated timestamp
  ... additional Google Places API fields ...
}
```

### Processed Places Collection Schema
```
{
  "_id": ObjectId,            // MongoDB document ID
  "name": String,             // Business/place name
  "address": String,          // Formatted address
  "city_slug": String,        // City slug (e.g. "seattle")
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
  "source_ids": {             // Original IDs from Google
    "google": String
  },
  "sources": Array,           // List of data sources ['google']
  "created_at": Date,         // Creation timestamp
  "updated_at": Date          // Last updated timestamp
}
```

## Tips for Efficient API and MongoDB Usage

### Google Places API (Free Credits - $200/month)
- Text searches cost about $0.04 per request (10,000 searches = $400)
- Place details cost about $0.006 per request (40,000 detail lookups = $240)
- The free $200 credit should allow for roughly 2,000-3,000 places per month
- Script automatically respects rate limits
- Our script fetches ALL available fields in the API response

### MongoDB Usage
- The system uses a single raw_places collection for all data
- When collecting new data, existing entries are updated rather than duplicated
- The processed_places collection contains deduplicated data
- For production, set up MongoDB authentication
- Consider setting up MongoDB Atlas for cloud-hosted access from your website

## Troubleshooting

**API Key Issues:**
- Ensure your Google Places API key is correctly entered in the `.env` file
- Make sure you've enabled the Places API in your Google Cloud Console

**MongoDB Connection Issues:**
- Check your MongoDB connection string in the `.env` file
- Ensure MongoDB is running on your system or Atlas is configured correctly
- Try connecting to MongoDB using the MongoDB shell or MongoDB Compass

**City Not Found:**
- Make sure you've added the city using the simple_city_fetcher.py script
- Check the city slug format (typically just the lowercase city name with hyphens, e.g. "new-york")
- Run `python src/data_collection/simple_city_fetcher.py --city "New York" --country "USA"` to add cities

**No Results Found:**
- Try different place types
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

The utility uses the Nominatim API from OpenStreetMap to geocode city names, retrieve location details, and extract state/province information. For US cities, it maps state names to their two-letter codes.

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
python src/data_collection/google_places_collector.py --city-slug "toronto" --type "escape_room"
```

This utility makes setting up and maintaining your city database entirely painless. You can now focus on collecting venue data rather than manually researching city details. 