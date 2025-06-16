import requests
import csv
from decouple import config

class CRMUpdater:
    def __init(self):
        self.base_url = "https://it-hiring.blackbird.vs"
        self.access_token = config('ACCESS_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        self.rate_limit_delay = (10 / 5) + 0.1 # Keep under 5 req per 10 secs

    def make_api_request(self, endpoint: str):
        """Make API requests with rate limiting and error handling"""
        pass

    def get_crm_data(self):
        """Get CRM contact data"""
        pass

    def get_form_submissions(self):
        """Fetch event feedback form submissions"""
        pass

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
        