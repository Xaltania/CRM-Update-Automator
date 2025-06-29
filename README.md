# Quick Start Guide

Create a `.env` file with your access token in the same directory as `.env`

Produced using python virtual environment.

Usage:

```bash
pip install -r requirements.txt
```

Run with
```bash
python script.py
```

with optional `-d | --debug` flags to get verbose output

# Implementation details

## Problem Analysis & Architecture Design
I designed a class-based Python solution (CRMUpdater) that follows a clear separation of concerns:

API Communication Layer: Handles rate-limited requests to both endpoints
Data Processing Layer: Normalises and matches data between CRM and form submissions
Business Logic Layer: Implements the core update logic with missing/outdated data detection
Output Layer: Generates the required CSV file with exact schema compliance

## API Integration Implementation
```python
def make_api_request(self, endpoint: str, response_format: str = 'json'):
```

Dual Format Support: Built flexible API client supporting both CSV (CRM endpoint) and JSON (form submissions endpoint)
Rate Limiting: Implemented 2.1-second delays to stay under 5 requests/10 seconds limit
Error Handling: Comprehensive exception handling for network issues, timeouts, and malformed responses
Authorisation: Proper Bearer token implementation using python-decouple for secure token management

## Data Normalisation Strategy
```python
def normalise_contact_data(self, contact):
def normalise_submission_data(self, submission):
```

Field Mapping: Created flexible field mapping to handle various possible column names from the form submissions API
Data Cleaning: Implemented .strip() on all fields to remove whitespace inconsistencies
Schema Standardisation: Converted both data sources to consistent internal format for processing

## Core Business Logic Implementation
```python
def is_data_missing_or_outdated(self, contact, submission):
```

Missing Data Detection: Checks for empty phone, first name, and last name fields
Date Comparison Logic: Compares submission dates with last contact dates to identify outdated records
Smart Update Criteria: Only flags records that actually need updating, preventing unnecessary data churn

## Data Preservation & Update Strategy
```python
def update_contact_with_feedback(self, contact, submission):
```

Append-Only History: Preserves existing "all contact text" by appending new feedback rather than replacing
Conditional Updates: Only fills missing fields, never overwrites existing data
Formatted Feedback: Creates professional feedback entries with dates, event info, and ratings when available

## Output Compliance
```python
def create_csv(self, contacts, filename: str = "crm-update.csv"):
```

Exact Schema Match: Uses the precise column names required: 'id', 'first', 'last', 'email', 'phone', 'last contact date', 'last contact text', 'all contact text'
Field Mapping: Maps internal normalised field names to the required CSV column structure
Complete Dataset: Outputs all contacts (updated and unchanged) to maintain CRM completeness

# Assumptions

## Data Quality Assumptions

Email as Primary Key: Assumed email addresses are the most reliable way to match contacts between systems
Date Format Consistency: Assumed dates follow ISO format or can be parsed by Python's datetime.fromisoformat()
Text Field Safety: Assumed contact text fields can contain newlines and need proper CSV escaping

## Business Logic Assumptions

Update Priority: Assumed newer feedback should update "last contact" fields even if contact was previously updated
Missing Data Importance: Assumed missing phone numbers and names are high priority to fill from form submissions
Contact History Value: Assumed preserving complete contact interaction history is more valuable than keeping entries short

## Operational Assumptions

Token Security: Assumed the provided access token should be stored in .env file for security
File Permissions: Assumed the script has write permissions in the current directory
Network Reliability: Assumed reasonable network connectivity with retry logic handled by the requests library

## Output Requirements Assumptions

Complete Dataset: Assumed the output CSV should contain ALL contacts, not just updated ones
Column Order: Assumed the exact column order specified in requirements must be maintained
UTF-8 Encoding: Assumed UTF-8 encoding for international characters in names and feedback

## Edge Case Assumptions

Duplicate Submissions: Assumed the same person might submit multiple feedback forms and all should be preserved
New Contacts: Assumed form submissions from people not in the CRM should be added as new contacts
Empty Feedback: Assumed submissions without feedback text should not trigger contact updates