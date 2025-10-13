import httpx
from mcp.server.fastmcp import FastMCP
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("Weather & Geocoding")

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"


@mcp.tool()
async def geocode_location(location: str) -> str:
    """
    Convert a location name (city, address, etc.) to coordinates.

    Args:
        location: Location name (e.g., "Paris, France" or "1600 Pennsylvania Ave, Washington DC")

    Returns:
        Latitude, longitude, and formatted address
    """
    headers = {
        "User-Agent": "WeatherGeocodingMCP/1.0 (Educational Purpose)"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }

            response = await client.get(f"{NOMINATIM_BASE}/search", params=params)
            response.raise_for_status()

            data = response.json()

            if not data:
                return f"Location not found: {location}"

            result = data[0]
            lat = result.get('lat')
            lon = result.get('lon')
            display_name = result.get('display_name')

            return f"Location: {display_name}\nLatitude: {lat}\nLongitude: {lon}"

        except Exception as e:
            return f"Error geocoding location: {str(e)}"


@mcp.tool()
async def reverse_geocode(latitude: float, longitude: float) -> str:
    """
    Convert coordinates to a location name.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Address and location information
    """
    headers = {
        "User-Agent": "WeatherGeocodingMCP/1.0 (Educational Purpose)"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json"
            }

            response = await client.get(f"{NOMINATIM_BASE}/reverse", params=params)
            response.raise_for_status()

            data = response.json()

            if 'error' in data:
                return f"Location not found for coordinates: {latitude}, {longitude}"

            display_name = data.get('display_name')
            address = data.get('address', {})

            result = f"Location: {display_name}\n\n"
            result += "Address Details:\n"

            for key, value in address.items():
                result += f"  {key.replace('_', ' ').title()}: {value}\n"

            return result.strip()

        except Exception as e:
            return f"Error reverse geocoding: {str(e)}"


@mcp.tool()
async def get_current_weather(location: str) -> str:
    """
    Get current weather for a location.

    Args:
        location: Location name (e.g., "London, UK" or "New York City")

    Returns:
        Current weather conditions including temperature, humidity, wind, etc.
    """
    headers = {
        "User-Agent": "WeatherGeocodingMCP/1.0 (Educational Purpose)"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            # First, geocode the location
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }

            response = await client.get(f"{NOMINATIM_BASE}/search", params=params)
            response.raise_for_status()
            geo_data = response.json()

            if not geo_data:
                return f"Location not found: {location}"

            lat = geo_data[0].get('lat')
            lon = geo_data[0].get('lon')
            display_name = geo_data[0].get('display_name')

            # Get weather data
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph"
            }

            weather_response = await client.get(f"{OPEN_METEO_BASE}/forecast", params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            current = weather_data.get('current', {})

            # Weather code descriptions
            weather_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }

            weather_code = current.get('weather_code', 0)
            weather_desc = weather_codes.get(weather_code, "Unknown")

            result = f"Current Weather for: {display_name}\n\n"
            result += f"Conditions: {weather_desc}\n"
            result += f"Temperature: {current.get('temperature_2m')}°F\n"
            result += f"Feels Like: {current.get('apparent_temperature')}°F\n"
            result += f"Humidity: {current.get('relative_humidity_2m')}%\n"
            result += f"Wind Speed: {current.get('wind_speed_10m')} mph\n"
            result += f"Wind Direction: {current.get('wind_direction_10m')}°\n"
            result += f"Precipitation: {current.get('precipitation')} mm\n"

            return result

        except Exception as e:
            return f"Error fetching weather: {str(e)}"


@mcp.tool()
async def get_weather_forecast(location: str, days: int = 7) -> str:
    """
    Get weather forecast for a location.

    Args:
        location: Location name (e.g., "Tokyo, Japan")
        days: Number of days to forecast (1-16, default: 7)

    Returns:
        Multi-day weather forecast
    """
    headers = {
        "User-Agent": "WeatherGeocodingMCP/1.0 (Educational Purpose)"
    }

    # Limit days to valid range
    days = max(1, min(days, 16))

    async with httpx.AsyncClient(headers=headers) as client:
        try:
            # Geocode location
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }

            response = await client.get(f"{NOMINATIM_BASE}/search", params=params)
            response.raise_for_status()
            geo_data = response.json()

            if not geo_data:
                return f"Location not found: {location}"

            lat = geo_data[0].get('lat')
            lon = geo_data[0].get('lon')
            display_name = geo_data[0].get('display_name')

            # Get forecast
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": days
            }

            weather_response = await client.get(f"{OPEN_METEO_BASE}/forecast", params=weather_params)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            daily = weather_data.get('daily', {})

            weather_codes = {
                0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 51: "Drizzle", 61: "Rain", 71: "Snow", 80: "Rain showers", 95: "Thunderstorm"
            }

            result = f"Weather Forecast for: {display_name}\n\n"

            for i in range(len(daily.get('time', []))):
                date = daily['time'][i]
                weather_code = daily['weather_code'][i]
                temp_max = daily['temperature_2m_max'][i]
                temp_min = daily['temperature_2m_min'][i]
                precip = daily['precipitation_sum'][i]
                wind = daily['wind_speed_10m_max'][i]

                weather_desc = weather_codes.get(weather_code, "Unknown")

                result += f"{date}:\n"
                result += f"  Conditions: {weather_desc}\n"
                result += f"  High: {temp_max}°F | Low: {temp_min}°F\n"
                result += f"  Precipitation: {precip} mm\n"
                result += f"  Max Wind: {wind} mph\n\n"

            return result.strip()

        except Exception as e:
            return f"Error fetching forecast: {str(e)}"


@mcp.tool()
async def get_weather_by_coordinates(latitude: float, longitude: float) -> str:
    """
    Get current weather by exact coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Current weather conditions for the coordinates
    """
    async with httpx.AsyncClient() as client:
        try:
            weather_params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph"
            }

            response = await client.get(f"{OPEN_METEO_BASE}/forecast", params=weather_params)
            response.raise_for_status()
            weather_data = response.json()

            current = weather_data.get('current', {})

            weather_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 51: "Drizzle", 61: "Rain", 71: "Snow", 80: "Rain showers", 95: "Thunderstorm"
            }

            weather_code = current.get('weather_code', 0)
            weather_desc = weather_codes.get(weather_code, "Unknown")

            result = f"Current Weather at ({latitude}, {longitude})\n\n"
            result += f"Conditions: {weather_desc}\n"
            result += f"Temperature: {current.get('temperature_2m')}°F\n"
            result += f"Feels Like: {current.get('apparent_temperature')}°F\n"
            result += f"Humidity: {current.get('relative_humidity_2m')}%\n"
            result += f"Wind Speed: {current.get('wind_speed_10m')} mph\n"
            result += f"Wind Direction: {current.get('wind_direction_10m')}°\n"
            result += f"Precipitation: {current.get('precipitation')} mm\n"

            return result

        except Exception as e:
            return f"Error fetching weather: {str(e)}"


def main():
    mcp.run()

if __name__ == "__main__":
    main()
