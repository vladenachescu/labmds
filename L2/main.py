import requests

def get_weather(city_name="Bucharest", lat=44.4323, lon=26.1063):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    print(f"Fetching current weather for {city_name} (from inside container)...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current_weather", {})
        temp = current.get("temperature")
        windspeed = current.get("windspeed")
        time = current.get("time")
        
        print("\n=== Weather Info ===")
        print(f"City: {city_name}")
        print(f"Temperature: {temp}°C")
        print(f"Wind Speed: {windspeed} km/h")
        print(f"Time: {time}")
        print("====================\n")
    except Exception as e:
        print(f"Error fetching weather data: {e}")

if __name__ == "__main__":
    get_weather()
