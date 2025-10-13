import httpx
from mcp.server.fastmcp import FastMCP
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("Countries & Currencies")

REST_COUNTRIES_BASE = "https://restcountries.com/v3.1"
EXCHANGE_RATE_BASE = "https://api.exchangerate-api.com/v4/latest"


@mcp.tool()
async def get_country_info(country: str) -> str:
    """
    Get detailed information about a country.

    Args:
        country: Country name or code (e.g., "France", "FR", "United States")

    Returns:
        Comprehensive country information including population, capital, languages, currencies, etc.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Try to search by name first
            url = f"{REST_COUNTRIES_BASE}/name/{country}"
            response = await client.get(url)

            # If not found by name, try by code
            if response.status_code == 404:
                url = f"{REST_COUNTRIES_BASE}/alpha/{country}"
                response = await client.get(url)

            response.raise_for_status()
            data = response.json()

            # Get first result if multiple matches
            country_data = data[0] if isinstance(data, list) else data

            name = country_data.get('name', {}).get('common', 'N/A')
            official_name = country_data.get('name', {}).get('official', 'N/A')
            capital = ', '.join(country_data.get('capital', ['N/A']))
            region = country_data.get('region', 'N/A')
            subregion = country_data.get('subregion', 'N/A')
            population = country_data.get('population', 0)
            area = country_data.get('area', 0)

            # Languages
            languages = country_data.get('languages', {})
            lang_str = ', '.join(languages.values()) if languages else 'N/A'

            # Currencies
            currencies = country_data.get('currencies', {})
            currency_list = []
            for code, curr_data in currencies.items():
                name_curr = curr_data.get('name', code)
                symbol = curr_data.get('symbol', '')
                currency_list.append(f"{name_curr} ({code}) {symbol}")
            currency_str = ', '.join(currency_list) if currency_list else 'N/A'

            # Other details
            timezones = ', '.join(country_data.get('timezones', ['N/A']))
            tld = ', '.join(country_data.get('tld', ['N/A']))
            calling_code = ', '.join([f"+{code}" for code in country_data.get('idd', {}).get('suffixes', [])])
            if country_data.get('idd', {}).get('root'):
                calling_code = country_data['idd']['root'] + calling_code

            # Borders
            borders = country_data.get('borders', [])
            borders_str = ', '.join(borders) if borders else 'None'

            result = f"🌍 {name}\n"
            result += f"{'=' * 50}\n\n"
            result += f"Official Name: {official_name}\n"
            result += f"Capital: {capital}\n"
            result += f"Region: {region} ({subregion})\n"
            result += f"Population: {population:,}\n"
            result += f"Area: {area:,} km²\n\n"
            result += f"💰 Currency: {currency_str}\n"
            result += f"🗣️ Languages: {lang_str}\n"
            result += f"🕐 Timezones: {timezones}\n"
            result += f"📞 Calling Code: {calling_code}\n"
            result += f"🌐 TLD: {tld}\n"
            result += f"🗺️ Borders: {borders_str}\n"

            # Flag
            flag = country_data.get('flag', '')
            if flag:
                result += f"\nFlag: {flag}"

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Country not found: {country}"
            return f"Error fetching country data: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def search_countries_by_region(region: str) -> str:
    """
    Get all countries in a specific region.

    Args:
        region: Region name (e.g., "Europe", "Asia", "Africa", "Americas", "Oceania")

    Returns:
        List of countries in the region with basic info
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{REST_COUNTRIES_BASE}/region/{region}"
            response = await client.get(url)
            response.raise_for_status()

            countries = response.json()

            result = f"Countries in {region.title()} ({len(countries)} total):\n\n"

            for country in sorted(countries, key=lambda x: x.get('name', {}).get('common', '')):
                name = country.get('name', {}).get('common', 'N/A')
                capital = ', '.join(country.get('capital', ['N/A']))
                population = country.get('population', 0)
                flag = country.get('flag', '')

                result += f"{flag} {name}\n"
                result += f"   Capital: {capital} | Population: {population:,}\n\n"

            return result.strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Region not found: {region}\nValid regions: Europe, Asia, Africa, Americas, Oceania"
            return f"Error fetching region data: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def search_countries_by_currency(currency_code: str) -> str:
    """
    Find all countries that use a specific currency.

    Args:
        currency_code: Currency code (e.g., "USD", "EUR", "GBP")

    Returns:
        List of countries using that currency
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{REST_COUNTRIES_BASE}/currency/{currency_code}"
            response = await client.get(url)
            response.raise_for_status()

            countries = response.json()

            # Get currency name from first country
            currency_name = "Unknown"
            if countries and currency_code.upper() in countries[0].get('currencies', {}):
                currency_name = countries[0]['currencies'][currency_code.upper()].get('name', currency_code)

            result = f"Countries using {currency_name} ({currency_code.upper()}):\n\n"

            for country in sorted(countries, key=lambda x: x.get('name', {}).get('common', '')):
                name = country.get('name', {}).get('common', 'N/A')
                flag = country.get('flag', '')
                population = country.get('population', 0)

                result += f"{flag} {name} (Pop: {population:,})\n"

            return result.strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"No countries found using currency: {currency_code}"
            return f"Error fetching currency data: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def search_countries_by_language(language: str) -> str:
    """
    Find all countries where a specific language is spoken.

    Args:
        language: Language name (e.g., "Spanish", "French", "Arabic")

    Returns:
        List of countries speaking that language
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{REST_COUNTRIES_BASE}/lang/{language}"
            response = await client.get(url)
            response.raise_for_status()

            countries = response.json()

            result = f"Countries speaking {language.title()} ({len(countries)} total):\n\n"

            for country in sorted(countries, key=lambda x: x.get('name', {}).get('common', '')):
                name = country.get('name', {}).get('common', 'N/A')
                flag = country.get('flag', '')
                region = country.get('region', 'N/A')
                population = country.get('population', 0)

                result += f"{flag} {name} ({region})\n"
                result += f"   Population: {population:,}\n\n"

            return result.strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"No countries found speaking: {language}"
            return f"Error fetching language data: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def get_exchange_rates(base_currency: str = "USD") -> str:
    """
    Get current exchange rates for a base currency.

    Args:
        base_currency: Base currency code (e.g., "USD", "EUR", "GBP")

    Returns:
        Exchange rates for all major currencies
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{EXCHANGE_RATE_BASE}/{base_currency.upper()}"
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()

            base = data.get('base', base_currency.upper())
            date = data.get('date', 'N/A')
            rates = data.get('rates', {})

            result = f"💱 Exchange Rates for {base}\n"
            result += f"Last Updated: {date}\n"
            result += f"{'=' * 50}\n\n"

            # Group by major currencies first
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR', 'MXN']

            result += "Major Currencies:\n"
            for currency in major_currencies:
                if currency in rates and currency != base:
                    rate = rates[currency]
                    result += f"  {currency}: {rate:.4f}\n"

            result += f"\nAll Rates ({len(rates)} currencies):\n"
            for currency, rate in sorted(rates.items()):
                if currency not in major_currencies or currency == base:
                    result += f"  {currency}: {rate:.4f}\n"

            return result.strip()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Currency not found: {base_currency}"
            return f"Error fetching exchange rates: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Convert an amount from one currency to another.

    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., "USD")
        to_currency: Target currency code (e.g., "EUR")

    Returns:
        Converted amount with exchange rate
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"{EXCHANGE_RATE_BASE}/{from_currency.upper()}"
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            rates = data.get('rates', {})

            if to_currency.upper() not in rates:
                return f"Currency not found: {to_currency}"

            rate = rates[to_currency.upper()]
            converted = amount * rate

            result = f"💰 Currency Conversion\n"
            result += f"{'=' * 50}\n\n"
            result += f"{amount:,.2f} {from_currency.upper()} = {converted:,.2f} {to_currency.upper()}\n\n"
            result += f"Exchange Rate: 1 {from_currency.upper()} = {rate:.4f} {to_currency.upper()}\n"
            result += f"Last Updated: {data.get('date', 'N/A')}"

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Currency not found: {from_currency}"
            return f"Error converting currency: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def compare_countries(country1: str, country2: str) -> str:
    """
    Compare two countries side by side.

    Args:
        country1: First country name or code
        country2: Second country name or code

    Returns:
        Side-by-side comparison of both countries
    """
    async with httpx.AsyncClient() as client:
        try:
            # Fetch both countries
            countries_data = []
            for country in [country1, country2]:
                url = f"{REST_COUNTRIES_BASE}/name/{country}"
                response = await client.get(url)

                if response.status_code == 404:
                    url = f"{REST_COUNTRIES_BASE}/alpha/{country}"
                    response = await client.get(url)

                response.raise_for_status()
                data = response.json()
                countries_data.append(data[0] if isinstance(data, list) else data)

            c1, c2 = countries_data

            result = f"🌍 Country Comparison\n"
            result += f"{'=' * 50}\n\n"

            name1 = c1.get('name', {}).get('common', 'N/A')
            name2 = c2.get('name', {}).get('common', 'N/A')

            result += f"{c1.get('flag', '')} {name1} vs {c2.get('flag', '')} {name2}\n\n"

            # Population
            pop1 = c1.get('population', 0)
            pop2 = c2.get('population', 0)
            result += f"Population:\n  {name1}: {pop1:,}\n  {name2}: {pop2:,}\n"
            result += f"  Difference: {abs(pop1-pop2):,}\n\n"

            # Area
            area1 = c1.get('area', 0)
            area2 = c2.get('area', 0)
            result += f"Area (km²):\n  {name1}: {area1:,}\n  {name2}: {area2:,}\n"
            result += f"  Difference: {abs(area1-area2):,}\n\n"

            # Region
            result += f"Region:\n  {name1}: {c1.get('region', 'N/A')} ({c1.get('subregion', 'N/A')})\n"
            result += f"  {name2}: {c2.get('region', 'N/A')} ({c2.get('subregion', 'N/A')})\n\n"

            # Capital
            cap1 = ', '.join(c1.get('capital', ['N/A']))
            cap2 = ', '.join(c2.get('capital', ['N/A']))
            result += f"Capital:\n  {name1}: {cap1}\n  {name2}: {cap2}\n\n"

            # Currency
            curr1 = list(c1.get('currencies', {}).keys())
            curr2 = list(c2.get('currencies', {}).keys())
            result += f"Currency:\n  {name1}: {', '.join(curr1) if curr1 else 'N/A'}\n"
            result += f"  {name2}: {', '.join(curr2) if curr2 else 'N/A'}\n"

            return result

        except Exception as e:
            return f"Error comparing countries: {str(e)}"


def main():
    mcp.run()

if __name__ == "__main__":
    main()
