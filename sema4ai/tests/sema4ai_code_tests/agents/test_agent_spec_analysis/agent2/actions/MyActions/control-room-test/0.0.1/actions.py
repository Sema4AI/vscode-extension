
import requests
from sema4ai.actions import action, Secret

@action(is_consequential=False)
def get_time_now(
        api_key: Secret,
        timezone: str
) -> str:
    """
    Returns the time in a given location right now.

    Args:
        api_key: Your API key to the service.
        timezone: Country/city information where to get the time at. Needs to be official timezone names, such as "Europe/London" or "America/New_York".

    Returns:
        Time object right now in the given location.
    """

    # Replace with your actual Vercel URL and API key
    vercel_url = "https://control-room-test-api.vercel.app/get-time"

    # Example data to send in the request
    data = {
        "country": timezone
    }

    # Headers including the API key
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "access_token": api_key.value
    }

    # Make the POST request
    response = requests.post(vercel_url, json=data, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        print("Success!")
        print("Response JSON:", response.json())
        return f"Time in location: {response.json()}"
    else:
        print("Failed!")
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())
        return f"Failed! Response JSON: {response.json()}"

