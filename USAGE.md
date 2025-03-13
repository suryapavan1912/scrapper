# Mental Health Resources Data Collector - Usage Guide

This guide provides step-by-step instructions for collecting data about mental health resources using the Yelp Fusion API (free tier) and Google Places API (with free credits).

## Prerequisites

1. Create accounts and obtain API keys:
   - [Yelp Fusion API](https://www.yelp.com/developers/documentation/v3/authentication) - Free tier with 500 calls/day
   - [Google Cloud Platform](https://developers.google.com/maps/documentation/places/web-service/get-api-key) - $200 free monthly credits

2. Set up your environment:
   ```bash
   # Clone the repository (if you haven't already)
   git clone <repository-url>
   cd <repository-directory>
   
   # Install required dependencies
   pip install -r requirements.txt
   
   # Create .env file with your API keys
   cp .env.example .env
   # Edit the .env file to add your actual API keys
   ```

## Step 1: Collect Data from Yelp API

The Yelp API is completely free (up to 500 calls/day) and provides rich data about businesses. Here's how to use it:

```bash
# Basic usage - search for escape rooms in Seattle
python src/data_collection/yelp_collector.py --city "Seattle, WA" --category "escapegames"

# Collect data about meditation centers in Portland
python src/data_collection/yelp_collector.py --city "Portland, OR" --category "meditationcenters"

# Limit results to 20 items
python src/data_collection/yelp_collector.py --city "New York, NY" --category "therapists" --max 20
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

## Step 2: Collect Data from Google Places API

Google Places API offers broader data but uses credits. The first $200 of usage each month is free:

```bash
# Basic usage - search for escape rooms in Seattle
python src/data_collection/google_places_collector.py --city "Seattle, WA" --type "escape_room"

# Collect data about museums in Portland
python src/data_collection/google_places_collector.py --city "Portland, OR" --type "museum"

# Limit results to 20 items
python src/data_collection/google_places_collector.py --city "New York, NY" --type "spa" --max 20
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

## Step 3: Combine Data from Both Sources

After collecting data from both APIs, you can combine them to create a comprehensive dataset:

```bash
# Basic usage - combine all data files in the data directory
python src/data_collection/combine_data.py

# Specify custom source and output directories
python src/data_collection/combine_data.py --source "data" --output "combined_data"
```

This will:
1. Load all Yelp and Google data files from the data directory
2. Normalize the data to a common format
3. Deduplicate entries that appear in both datasets
4. Save the combined data as JSON and CSV files

## Tips for Efficient API Usage

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

## Adding More Categories or Place Types

To add more categories or place types:

1. Open the appropriate collector file:
   - `src/data_collection/yelp_collector.py` for Yelp categories
   - `src/data_collection/google_places_collector.py` for Google place types

2. Add your new categories/types to the `VALID_CATEGORIES` or `VALID_PLACE_TYPES` lists

For Yelp categories, refer to: https://www.yelp.com/developers/documentation/v3/category_list
For Google place types, refer to: https://developers.google.com/maps/documentation/places/web-service/supported_types

## Troubleshooting

**API Key Issues:**
- Ensure your API keys are correctly entered in the `.env` file
- For Google, make sure you've enabled the Places API in your Google Cloud Console

**No Results Found:**
- Try different category/type terms
- Ensure the location is valid
- Try a larger, more well-known city first

**Rate Limiting:**
- If you hit rate limits, the script will automatically slow down
- For persistent issues, reduce the `--max` parameter 