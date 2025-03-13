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

### Collecting Data from Yelp (Free Tier)
```
python src/data_collection/yelp_collector.py --city "City Name" --category "Category Name"
```

### Collecting Data from Google Places (Free Credits)
```
python src/data_collection/google_places_collector.py --city "City Name" --type "Place Type"
```

## Available Categories/Types

### Yelp Categories
- escapegames
- arcades
- meditationcenters
- yoga
- psychologists
- therapists

### Google Place Types
- amusement_park
- art_gallery
- bowling_alley
- escape_room
- gym
- spa
- psychologist
- health

## Output

Data is saved in the `data/` directory in JSON format.

## API Limitations

- Yelp Fusion API: 500 calls/day with the free tier
- Google Places API: $200 free monthly credits, then pay-per-use 