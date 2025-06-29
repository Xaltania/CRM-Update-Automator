import io
import time
import requests
import csv
from decouple import config

ENDPOINTS_DATA = '/api/data/crm'
ENDPOINTS_SUBMISSION = '/api/data/form-submissions'


class CRMUpdater:
    def __init__(self):
        self.base_url = "https://it-hiring.blackbird.vc"
        self.access_token = config('ACCESS_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        self.rate_limit_delay = (10 / 5) + 0.1 # Keep < 5 req / 10s

    def make_api_request(self, endpoint: str):
        """Make API requests with rate limiting and error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"Making request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            time.sleep(self.rate_limit_delay)

            print(f"Status code: {response.status_code}")
            print(f"Raw response: {repr(response.text)}")

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as json_err:
                    print(f"JSON decode error: {json_err}")
                    return None
            else:
                print(f"API Request failed: STATUS {response.status_code}: {response.text}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None


    def get_crm_data(self):
        """Get CRM contact data"""
        print("Fetching CRM contact data...")
        response_text = self.make_api_request(ENDPOINTS_DATA)

        if not response_text:
            print("No CRM data found or invalid response format")
            return []

        try:
            # Convert CSV string to list of dicts
            csv_file = io.StringIO(response_text)
            reader = csv.DictReader(csv_file)
            return list(reader)
        except Exception as e:
            print(f"CSV parsing error: {e}")
            return []

    def get_form_submissions(self):
        """Fetch event feedback form submissions"""
        print("Getting submission form....")
        data = self.make_api_request(ENDPOINTS_SUBMISSION)

    def normalise_contact_data(self, contact):
        """Normalise the contact data structure"""
        pass

    def normalise_submission_data(self, submission):
        """Normalise form submission data stucture"""
        pass

    # Need some form of error checking for missing/outdated requirement.

    def update_contact_with_feedback(self, contact, submission):
        """Update contact record with the feedback data"""
        pass

    def process_and_update_contacts(self):
        """Main processing logic to update contacts with feedback"""
        pass

    def create_csv(self, contacts, filename: str = "crm_update.csv"):
        """Create CSV file with updated contact data"""
        pass

    def run(self):
        """Run the updater"""
        print("Starting CRM update automation")
        print(f"Using token: {self.access_token[:5]}...")



if __name__ == "__main__":
    import os
    if not os.path.exists('.env'):
        print("Unable to locate .env! You need it to authorise yourself" \
        "with the api")
    updater = CRMUpdater()
    print(updater.get_crm_data())