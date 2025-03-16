# Mental Health Resources Data Collector

This project collects data about therapeutic and stress-relief locations like rage rooms, escape rooms, etc., for a mental health resources website.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your API keys:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file with your actual API keys

## Usage

### Collecting Data from Google Places (Free Credits)
```
python src/data_collection/google_places_collector.py --city-slug "city-slug" --type "place-type"
```

Example:
```
python src/data_collection/google_places_collector.py --city-slug "seattle" --type "escape-room" --max 20
```

## Available Categories/Types

### Google Place Types
- amusement-park
- art-gallery
- bowling-alley
- escape-room
- gym
- spa
- psychologist
- health
- park
- museum
- movie-theater
- rage-room

## Effective Search Queries

The Google Places collector uses optimized search queries for each place type to get the best results. Some examples:

- Escape Rooms: "top rated escape rooms in [city]"
- Rage Rooms: "rage rooms in [city]"
- Mental Health: "mental health centers in [city]"
- Parks: "relaxing parks in [city]"
- Museums: "interactive museums in [city]"

See the `get_search_query()` function in the collector for the full list of templates.

## Output

Data is saved to MongoDB in the `raw_places` collection. Each place record includes the category it was collected under.

## API Limitations

- Google Places API: $200 free monthly credits, then pay-per-use 