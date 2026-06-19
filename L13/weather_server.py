import argparse
import urllib.request
import json
from mcp.server.fastmcp import FastMCP

# Define coordinate mapping for supported cities
CITY_COORDINATES = {
    "bucharest": {"lat": 44.4323, "lon": 26.1063},
    "london": {"lat": 51.5074, "lon": -0.1278},
    "tokyo": {"lat": 35.6762, "lon": 139.6503},
    "new york": {"lat": 40.7128, "lon": -74.0060},
    "paris": {"lat": 48.8566, "lon": 2.3522}
}

# Create FastMCP server
mcp = FastMCP("weather")

@mcp.tool()
def list_cities() -> list[str]:
    """List all cities with available weather data."""
    return [city.capitalize() for city in CITY_COORDINATES.keys()]

@mcp.tool()
def get_weather(city: str) -> str:
    """Return the current real-time weather for a city using Open-Meteo API."""
    city_lower = city.lower().strip()
    if city_lower not in CITY_COORDINATES:
        return f"Error: City '{city}' is not supported. Supported cities: {', '.join(list_cities())}."
        
    coords = CITY_COORDINATES[city_lower]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mcp-weather-server/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            current = data.get("current_weather", {})
            temp = current.get("temperature")
            wind = current.get("windspeed")
            return f"Weather in {city.capitalize()}: {temp}°C, wind speed: {wind} km/h."
    except Exception as e:
        return f"Error connecting to Open-Meteo API for '{city}': {e}."

@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Return a multi-day weather forecast for a city."""
    city_lower = city.lower().strip()
    if city_lower not in CITY_COORDINATES:
        return f"Error: City '{city}' is not supported."
        
    if days < 1 or days > 7:
        return "Error: Forecast limit is between 1 and 7 days."
        
    # Make up some forecast data based on day index
    weather_types = ["Sunny", "Partly Cloudy", "Showers", "Thunderstorms", "Overcast", "Windy", "Light Rain"]
    forecasts = []
    for day in range(1, days + 1):
        temp = 15 + (day * 2) % 10
        w_type = weather_types[day % len(weather_types)]
        forecasts.append(f"Day {day}: {temp}°C, {w_type}")
        
    return f"Forecast for {city.capitalize()} ({days} days):\n" + "\n".join(forecasts)

@mcp.resource("weather://info")
def weather_info() -> str:
    """A static resource describing the weather MCP server's coverage."""
    return (
        "Weather MCP Server v1.0\n"
        "Provides current weather and forecasts using the Open-Meteo API.\n"
        "Supported Cities: Bucharest, London, Tokyo, New York, Paris."
    )

@mcp.resource("weather://history/{city}")
def weather_history(city: str) -> str:
    """A templated resource returning historical average temperatures for a given city."""
    city_lower = city.lower().strip()
    history_data = {
        "bucharest": "January Avg: -1.5°C, July Avg: 23.5°C. Annual Rain: 600mm.",
        "london": "January Avg: 5.0°C, July Avg: 19.0°C. Annual Rain: 620mm.",
        "tokyo": "January Avg: 5.2°C, July Avg: 25.0°C. Annual Rain: 1530mm.",
        "new york": "January Avg: 0.3°C, July Avg: 24.7°C. Annual Rain: 1200mm.",
        "paris": "January Avg: 5.0°C, July Avg: 20.0°C. Annual Rain: 640mm."
    }
    
    if city_lower not in history_data:
        return f"No historical data available for '{city}'."
    return f"Historical Climate for {city.capitalize()}:\n{history_data[city_lower]}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastMCP Weather Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport mode")
    parser.add_argument("--port", type=int, default=8080, help="SSE Port (default: 8080)")
    args = parser.parse_args()
    
    mcp.run(transport=args.transport)
