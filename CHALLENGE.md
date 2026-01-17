# uOttawaHack8 Trajectory Insight Challenge

Create a tool for the national flight planning center that extracts insights from a list of daily planned flights and proposes solutions for conflicts and hot spots while taking into account cost and efficiency.  The idea is that air traffic planners will use the insights from your tool to adjust the planned flight operations. Feel free to use the flight planning data above, or create your own synthetic data.

## ⚠️ Data Disclaimer

**IMPORTANT: This is synthetic data for hackathon purposes only.**

### Not for Operational Use

- ❌ **DO NOT use this data for actual flight planning, air traffic control, or aviation operations**
- ❌ This data does not represent real flights, schedules, or aircraft positions
- ❌ Airport coordinates are approximate and simplified for visualization purposes
- ❌ Waypoints are fictional and do not represent actual navigation routes
- ❌ Aircraft performance characteristics are generalized approximations


## JSON Format

### Structure

```json
[
  {
    "ACID": "ACA101",
    "Plane type": "Boeing 787-9",
    "route": "49.97N/110.935W 49.64N/92.114W",
    "altitude": 37000,
    "departure airport": "CYYZ",
    "arrival airport": "CYVR",
    "departure time": 1736244000,
    "aircraft speed": 485.0,
    "passengers": 280,
    "is_cargo": false
  }
]
```

### Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `ACID` | string | Flight callsign (3-letter airline + 3 digits) | `"ACA101"` |
| `Plane type` | string | Aircraft model | `"Boeing 787-9"` |
| `route` | string | Space-separated waypoints in format LAT°N/LON°W. These are the points that the aircraft will fly between departure and arrival airport. | `"49.97N/110.935W 49.64N/92.114W"` |
| `altitude` | integer | Cruising altitude in feet | `37000` |
| `departure airport` | string | ICAO airport code | `"CYYZ"` |
| `arrival airport` | string | ICAO airport code | `"CYVR"` |
| `departure time` | integer | Unix timestamp (UTC) | `1736244000` |
| `aircraft speed` | float | Ground speed in knots | `485.0` |
| `passengers` | integer | Number of passengers (0 for cargo) | `280` |
| `is_cargo` | boolean | Whether this is a cargo flight | `false` |


### Time Format

All `departure time` values are Unix timestamps representing seconds since January 1, 1970, in UTC.

**Example Conversions:**
- 5:00 AM EST → 10:00 AM UTC → `1736244000`
- 12:00 PM EST → 5:00 PM UTC → `1736269200`
- 6:00 PM EST → 11:00 PM UTC → `1736290800`
- 11:59 PM EST → 4:59 AM UTC (next day) → `1736312340`

---

## Reference Data

### Canadian Airports (ICAO Codes)

| Code | Airport | City | Latitude | Longitude |
|------|---------|------|----------|-----------|
| CYYZ | Toronto Pearson | Toronto, ON | 43.68°N | 79.63°W |
| CYVR | Vancouver International | Vancouver, BC | 49.19°N | 123.18°W |
| CYUL | Montreal-Trudeau | Montreal, QC | 45.47°N | 73.74°W |
| CYYC | Calgary International | Calgary, AB | 51.11°N | 114.02°W |
| CYOW | Ottawa Macdonald-Cartier | Ottawa, ON | 45.32°N | 75.67°W |
| CYWG | Winnipeg Richardson | Winnipeg, MB | 49.91°N | 97.24°W |
| CYHZ | Halifax Stanfield | Halifax, NS | 44.88°N | 63.51°W |
| CYEG | Edmonton International | Edmonton, AB | 53.31°N | 113.58°W |
| CYQB | Quebec City Jean Lesage | Quebec City, QC | 46.79°N | 71.39°W |
| CYYJ | Victoria International | Victoria, BC | 48.65°N | 123.43°W |
| CYYT | St. John's International | St. John's, NL | 47.62°N | 52.75°W |
| CYXE | Saskatoon International | Saskatoon, SK | 52.17°N | 106.70°W |

### Aircraft Types

**Passenger Aircraft:**
- Wide-body: `Boeing 787-9`, `Boeing 777-300ER`, `Airbus A330`
- Narrow-body: `Boeing 737-800`, `Boeing 737 MAX 8`, `Airbus A320`, `Airbus A321`, `Airbus A220-300`
- Regional: `Dash 8-400`, `Embraer E195-E2`

**Cargo Aircraft:**
- `Boeing 767-300F`
- `Boeing 757-200F`
- `Airbus A300-600F`

### Common Waypoints

```
49.97N/110.935W  (Alberta/Saskatchewan border)
49.64N/92.114W   (Manitoba)
45.88N/78.031W   (Eastern Ontario)
50.18N/71.405W   (Quebec)
49.82N/86.449W   (Northern Ontario)
52.45N/105.22W   (Central Saskatchewan)
48.22N/118.55W   (British Columbia)
46.15N/84.33W    (Northern Ontario)
47.50N/69.88W    (Eastern Quebec)
51.33N/100.44W   (Central Manitoba)
50.77N/115.66W   (Alberta Rockies)
44.55N/75.22W    (Eastern Ontario)
```

---

## Constraints

### Altitude Constraints

| Aircraft Type | Minimum Altitude | Maximum Altitude | Optimal Range |
|---------------|------------------|------------------|---------------|
| Regional (Dash 8, E195) | 22,000 ft | 28,000 ft | 24,000-26,000 ft |
| Narrow-body (737, A320, A321) | 28,000 ft | 39,000 ft | 33,000-37,000 ft |
| Wide-body (787, 777, A330) | 31,000 ft | 43,000 ft | 37,000-41,000 ft |
| Cargo (767F, 757F, A300F) | 28,000 ft | 41,000 ft | 35,000-39,000 ft |

### Speed Constraints
| Aircraft Type | Cruise Speed | Minimum Speed | Maximum Speed |
|---------------|--------------|---------------|---------------|
| Turboprops (Dash 8) | 360 knots | 310 knots | 410 knots |
| Regional jets (E195, A220) | 420-450 knots | 370 knots | 500 knots |
| Narrow-body (737, A320, A321) | 465-485 knots | 415 knots | 505 knots |
| Wide-body (787, 777, A330) | 480-505 knots | 430 knots | 505 knots |
| Cargo (767F, 757F, A300F) | 460-480 knots | 410 knots | 505 knots |

## Loss-of-Separation Detection

A loss-of-separation occurs when **both** conditions are simultaneously met:

1. **Horizontal Separation** < 5 nautical miles
2. **Vertical Separation** < 2,000 feet


---


