import io
import time
import requests
import csv
from datetime import datetime
from decouple import config
import argparse

ENDPOINTS_DATA = '/api/data/crm'
ENDPOINTS_SUBMISSION = '/api/data/form-submissions'

class CRMUpdater:
    def __init__(self, debug=False):
        self.base_url = "https://it-hiring.blackbird.vc"
        self.access_token = config('ACCESS_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        self.rate_limit_delay = (10 / 5) + 0.1  # Keep < 5 req / 10s
        self.debug = debug

    def make_api_request(self, endpoint: str, response_format: str = 'json'):
        """Make API requests with rate limiting and error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if self.debug:
                print(f"Making request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            time.sleep(self.rate_limit_delay)
            
            if self.debug:
                print(f"Status code: {response.status_code}")
                print(f"Raw response: {repr(response.text)[:300]}...")

            if response.status_code == 200:
                if response_format == 'json':
                    try:
                        return response.json()
                    except ValueError as json_err:
                        if self.debug:
                            print(f"JSON decode error: {json_err}")
                        return None
                elif response_format == 'csv':
                    return response.text
                else:
                    if self.debug:
                        print(f"Unknown response format: {response_format}")
                    return None
            else:
                if self.debug:
                    print(f"API Request failed: STATUS {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            if self.debug:
                print(f"Request Error: {e}")
            return None

    def get_crm_data(self):
        """Get CRM contact data"""
        print("Fetching CRM contact data...")
        response_text = self.make_api_request(ENDPOINTS_DATA, response_format='csv')
        
        if not response_text:
            print("No CRM data found or invalid response format")
            return []
        
        try:
            csv_file = io.StringIO(response_text)
            reader = csv.DictReader(csv_file)
            contacts = list(reader)
            print(f"Successfully parsed {len(contacts)} CRM contacts")
            return contacts
        except Exception as e:
            print(f"CSV parsing error: {e}")
            return []

    def get_form_submissions(self):
        """Fetch event feedback form submissions"""
        print("Getting submission form data...")
        data = self.make_api_request(ENDPOINTS_SUBMISSION, response_format='json')
        
        if not data:
            print("No form submission data found or invalid response format")
            return []
        
        # Handle different possible response structures
        if isinstance(data, dict):
            if 'data' in data:
                return data['data']
            elif 'submissions' in data:
                return data['submissions']
            else:
                return [data]  # Single submission wrapped in dict
        elif isinstance(data, list):
            return data
        else:
            if self.debug:
                print(f"Unexpected data format for submissions: {type(data)}")
            return []

    def normalise_contact_data(self, contact):
        """Normalise the contact data structure to match CRM schema"""
        # The CRM data uses exact column names with spaces
        return {
            'id': contact.get('id', '').strip(),
            'first': contact.get('first', '').strip(),
            'last': contact.get('last', '').strip(),
            'email': contact.get('email', '').strip(),
            'phone': contact.get('phone', '').strip(),
            'last_contact_date': contact.get('last contact date', '').strip(),
            'last_contact_text': contact.get('last contact text', '').strip(),
            'all_contact_text': contact.get('all contact text', '').strip()
        }

    def normalise_submission_data(self, submission):
        """Normalise form submission data structure"""
        # Handle various possible field names from the form submissions API
        normalised = {
            'id': '',
            'first': '',
            'last': '',
            'email': '',
            'phone': '',
            'feedback': '',
            'submission_date': '',
            'event': '',
            'rating': ''
        }
        
        # Map common field variations
        field_mappings = {
            'id': ['id', 'contact_id', 'user_id', 'submission_id'],
            'first': ['first', 'first_name', 'firstName', 'fname'],
            'last': ['last', 'last_name', 'lastName', 'lname'],
            'email': ['email', 'email_address', 'user_email'],
            'phone': ['phone', 'phone_number', 'mobile', 'telephone'],
            'feedback': ['feedback', 'comments', 'message', 'review', 'notes'],
            'submission_date': ['submission_date', 'created_at', 'timestamp', 'date', 'submitted_at'],
            'event': ['event', 'event_name', 'event_title'],
            'rating': ['rating', 'score', 'satisfaction']
        }
        
        for normalised_key, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in submission and submission[key]:
                    normalised[normalised_key] = str(submission[key]).strip()
                    break
        
        return normalised

    def is_data_missing_or_outdated(self, contact, submission):
        """Check if contact data is missing or outdated compared to submission"""
        
        # Check for missing essential data that submission can provide
        if not contact.get('phone') and submission.get('phone'):
            if self.debug:
                print(f"  Missing phone for {contact.get('email', 'unknown')}")
            return True
        
        if not contact.get('first') and submission.get('first'):
            if self.debug:
                print(f"  Missing first name for {contact.get('email', 'unknown')}")
            return True
            
        if not contact.get('last') and submission.get('last'):
            if self.debug:
                print(f"  Missing last name for {contact.get('email', 'unknown')}")
            return True
        
        # Check if submission provides new feedback
        if submission.get('feedback'):
            # If no last contact date, definitely update
            if not contact.get('last_contact_date'):
                if self.debug:
                    print(f"  No last contact date for {contact.get('email', 'unknown')}")
                return True
                
            # Check if submission is more recent than last contact
            try:
                submission_date_str = submission.get('submission_date', '')
                last_contact_date_str = contact.get('last_contact_date', '')
                
                if submission_date_str and last_contact_date_str:
                    # Parse dates (handle various formats)
                    submission_date = datetime.fromisoformat(submission_date_str.replace('s', '+00:00').split('T')[0])
                    last_contact_date = datetime.fromisoformat(last_contact_date_str.replace('s', '+00:00').split('T')[0])
                    
                    if submission_date > last_contact_date:
                        if self.debug:
                            print(f"  Newer feedback available for {contact.get('email', 'unknown')}")
                        return True
            except (ValueError, TypeError) as e:
                if self.debug:
                    print(f"  Date parsing issue for {contact.get('email', 'unknown')}: {e}")
                # If date parsing fails, assume we should update
                return True
        
        return False

    def update_contact_with_feedback(self, contact, submission):
        """Update contact record with the feedback data"""
        updated_contact = contact.copy()
        
        # Update missing fields
        if not updated_contact.get('phone') and submission.get('phone'):
            updated_contact['phone'] = submission['phone']
            if self.debug:
                print(f"    Added phone: {submission['phone']}")
        
        if not updated_contact.get('first') and submission.get('first'):
            updated_contact['first'] = submission['first']
            if self.debug:
                print(f"    Added first name: {submission['first']}")
            
        if not updated_contact.get('last') and submission.get('last'):
            updated_contact['last'] = submission['last']
            if self.debug:
                print(f"    Added last name: {submission['last']}")
        
        # Update contact information with feedback
        if submission.get('feedback'):
            # Format the feedback message
            event_info = f" about {submission['event']}" if submission.get('event') else ""
            rating_info = f" (Rating: {submission['rating']})" if submission.get('rating') else ""
            
            feedback_text = f"Event feedback{event_info}: {submission['feedback']}{rating_info}"
            
            # Update last contact info
            updated_contact['last_contact_text'] = feedback_text
            updated_contact['last_contact_date'] = submission.get('submission_date', datetime.now().strftime('%Y-%m-%d'))
            
            # Append to all contact text (preserve existing history)
            existing_text = updated_contact.get('all_contact_text', '').strip()
            new_entry = f"{updated_contact['last_contact_date']} - {feedback_text}"
            
            if existing_text:
                updated_contact['all_contact_text'] = f"{existing_text}\n \n {new_entry}"
            else:
                updated_contact['all_contact_text'] = new_entry
                
            if self.debug:
                print(f"    Added feedback: {submission['feedback'][:50]}...")
        
        return updated_contact

    def process_and_update_contacts(self):
        """Main processing logic to update contacts with feedback"""
        print("Processing contact updates...")
        
        # Get data from both endpoints
        crm_contacts = self.get_crm_data()
        form_submissions = self.get_form_submissions()
        
        if not crm_contacts:
            print("No CRM contacts found")
            return []
        
        # Normalise data
        normalised_contacts = [self.normalise_contact_data(contact) for contact in crm_contacts]
        normalised_submissions = [self.normalise_submission_data(sub) for sub in form_submissions]
        
        print(f"Processing {len(normalised_contacts)} contacts with {len(normalised_submissions)} submissions")
        
        # Create lookup dictionaries for submissions
        submissions_by_email = {}
        submissions_by_id = {}
        
        for submission in normalised_submissions:
            if submission.get('email'):
                email_key = submission['email'].lower()
                if email_key not in submissions_by_email:
                    submissions_by_email[email_key] = []
                submissions_by_email[email_key].append(submission)
            
            if submission.get('id'):
                id_key = submission['id']
                if id_key not in submissions_by_id:
                    submissions_by_id[id_key] = []
                submissions_by_id[id_key].append(submission)
        
        updated_contacts = []
        update_count = 0
        
        for contact in normalised_contacts:
            # Try to find matching submissions
            matching_submissions = []
            
            # First try to match by contact ID
            if contact.get('id') and contact['id'] in submissions_by_id:
                matching_submissions.extend(submissions_by_id[contact['id']])
            
            # Then try to match by email
            if contact.get('email') and contact['email'].lower() in submissions_by_email:
                matching_submissions.extend(submissions_by_email[contact['email'].lower()])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_submissions = []
            for sub in matching_submissions:
                sub_key = (sub.get('email', ''), sub.get('feedback', ''), sub.get('submission_date', ''))
                if sub_key not in seen:
                    seen.add(sub_key)
                    unique_submissions.append(sub)
            
            # Process each matching submission
            current_contact = contact
            contact_updated = False
            
            for submission in unique_submissions:
                if self.is_data_missing_or_outdated(current_contact, submission):
                    print(f"Updating contact: {current_contact.get('email', 'Unknown email')}")
                    current_contact = self.update_contact_with_feedback(current_contact, submission)
                    contact_updated = True
            
            if contact_updated:
                update_count += 1
            
            updated_contacts.append(current_contact)
        
        print(f"Updated {update_count} contacts out of {len(normalised_contacts)}")
        
        # Add any new contacts from submissions that don't exist in CRM
        existing_emails = {contact.get('email', '').lower() for contact in normalised_contacts if contact.get('email')}
        existing_ids = {contact.get('id') for contact in normalised_contacts if contact.get('id')}
        
        new_contact_count = 0
        for submission in normalised_submissions:
            submission_email = submission.get('email', '').lower()
            submission_id = submission.get('id')
            
            # Check if this is a completely new contact
            if (submission_email and submission_email not in existing_emails and 
                submission_id and submission_id not in existing_ids and
                submission.get('feedback')):
                
                # Create new contact from submission
                event_info = f" about {submission['event']}" if submission.get('event') else ""
                rating_info = f" (Rating: {submission['rating']})" if submission.get('rating') else ""
                feedback_text = f"Event feedback{event_info}: {submission['feedback']}{rating_info}"
                
                new_contact = {
                    'id': submission_id or f"new-{len(updated_contacts) + 1}",
                    'first': submission.get('first', ''),
                    'last': submission.get('last', ''),
                    'email': submission.get('email', ''),
                    'phone': submission.get('phone', ''),
                    'last_contact_date': submission.get('submission_date', datetime.now().strftime('%Y-%m-%d')),
                    'last_contact_text': feedback_text,
                    'all_contact_text': f"{submission.get('submission_date', datetime.now().strftime('%Y-%m-%d'))} - {feedback_text}"
                }
                updated_contacts.append(new_contact)
                new_contact_count += 1
                print(f"Added new contact from submission: {new_contact.get('email', 'Unknown email')}")
        
        if new_contact_count > 0:
            print(f"Added {new_contact_count} new contacts from submissions")
        
        return updated_contacts

    def create_csv(self, contacts, filename: str = "crm-update.csv"):
        """Create CSV file with updated contact data using required schema"""
        if not contacts:
            print("No contacts to write to CSV")
            return
        
        print(f"Creating CSV file: {filename}")
        
        # Use the exact required column names
        fieldnames = ['id', 'first', 'last', 'email', 'phone', 'last contact date', 'last contact text', 'all contact text']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for contact in contacts:
                    # Map our normalised field names to the required CSV column names
                    row = {
                        'id': contact.get('id', ''),
                        'first': contact.get('first', ''),
                        'last': contact.get('last', ''),
                        'email': contact.get('email', ''),
                        'phone': contact.get('phone', ''),
                        'last contact date': contact.get('last_contact_date', ''),
                        'last contact text': contact.get('last_contact_text', ''),
                        'all contact text': contact.get('all_contact_text', '')
                    }
                    writer.writerow(row)
            
            print(f"Successfully created CSV file: {filename}")
            print(f"Wrote {len(contacts)} contacts to file")
            
        except Exception as e:
            print(f"Error creating CSV file: {e}")

    def download_original_csv(self, filename: str = "original_crm_contacts.csv"):
        """Download and save the original CRM CSV file for comparison"""
        if self.debug:
            print(f"Downloading original CRM CSV to {filename}...")
        response_text = self.make_api_request(ENDPOINTS_DATA, response_format='csv')
        if not response_text:
            print("Failed to download original CRM CSV.")
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response_text)
            if self.debug:
                print(f"Original CRM CSV saved as {filename}")
        except Exception as e:
            print(f"Error saving original CRM CSV: {e}")

    def run(self):
        """Run the updater"""
        print("Starting CRM update automation...")
        if self.debug:
            print(f"Using token: {self.access_token[:5]}...")
        
        # Download the original CRM CSV for comparison (only in debug mode)
        if self.debug:
            self.download_original_csv()
        
        # Process and update contacts
        updated_contacts = self.process_and_update_contacts()
        
        if updated_contacts:
            # Create the required output file
            self.create_csv(updated_contacts, "crm-update.csv")
            
            # Count contacts with recent updates
            recent_updates = sum(1 for contact in updated_contacts 
                               if contact.get('last_contact_text', '').startswith('Event feedback'))
            
            print(f"\nProcessing Summary:")
            print(f"Total contacts: {len(updated_contacts)}")
            print(f"Contacts updated with new feedback: {recent_updates}")
            print(f"Output file: crm-update.csv")
        else:
            print("No contacts were processed")

if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser(description="CRM Update Automator")
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    if not os.path.exists('.env'):
        print("Could not locate .env file...")
    else:
        updater = CRMUpdater(debug=args.debug)
        updater.run()