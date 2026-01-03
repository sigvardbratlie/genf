#!/usr/bin/env python3
"""
Complete API Documentation and Proof of Concept Script
=======================================================

This script serves as comprehensive documentation for the Community Odd Jobs API.
It demonstrates all available API endpoints and their usage patterns.

API Endpoints:
-------------
1. get_profiles_with_api_key(p_api_key)
   - Fetches all user profiles for the organization
   - Returns: id, first_name, last_name, phone, role, availability_notes,
              created_at, updated_at, organization_id, monthly_goal,
              date_of_birth, age_category, bank_account_number, custom_id

2. get_work_requests_with_api_key(p_api_key, p_from_date, p_to_date)
   - Fetches work requests (jobs) for the organization
   - Optional date filtering by creation date
   - Returns: All work request fields including status, payment details, etc.

3. get_job_logs_with_api_key(p_api_key, p_from_date, p_to_date)
   - Fetches completed work logs (job registrations)
   - Optional date filtering by completion date
   - Returns: All job log fields including worker names, hours, rates, etc.

4. get_job_applications_with_api_key(p_api_key, p_work_request_id)
   - Fetches job applications for a specific work request
   - Returns: Application details with user information

Requirements:
    pip install supabase python-dotenv

Configuration:
    Set environment variables or update constants below:
    - SUPABASE_URL
    - SUPABASE_ANON_KEY
    - API_KEY

Usage Examples:
    # Fetch all profiles
    python api_complete_documentation.py --profiles

    # Fetch work requests with date range
    python api_complete_documentation.py --work-requests --from-date 2025-01-01 --to-date 2025-01-31

    # Fetch job logs and export to CSV
    python api_complete_documentation.py --job-logs --csv --from-date 2025-01-01

    # Fetch job applications for a specific work request
    python api_complete_documentation.py --job-applications <work_request_id>

    # Test all endpoints
    python api_complete_documentation.py --all
"""

import os
import sys
import argparse
import csv
import json
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install supabase python-dotenv")
    sys.exit(1)

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration - Update these or set as environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qvkdyodpfauvpsamrmew.supabase.co")
SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2a2R5b2RwZmF1dnBzYW1ybWV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzNzMyMDEsImV4cCI6MjA2NDk0OTIwMX0.gMscCXj733-_cT87_ErXPHaaa3YQdWE5gjpJ8XZ4yXI"
)
API_KEY = os.getenv("API_KEY", "")


# ============================================================================
# API ENDPOINT FUNCTIONS
# ============================================================================

def fetch_profiles(supabase: Client, api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all user profiles for the organization.
    
    API Function: get_profiles_with_api_key(p_api_key text)
    
    Returns:
        List of profile dictionaries with the following fields:
        - id (uuid): User's unique identifier
        - first_name (text): User's first name
        - last_name (text): User's last name
        - phone (text): User's phone number
        - role (user_role): User's role ('admin' or 'member')
        - availability_notes (text): Notes about user availability
        - created_at (timestamp): Account creation timestamp
        - updated_at (timestamp): Last update timestamp
        - organization_id (uuid): Organization identifier
        - monthly_goal (integer): Monthly work hour goal
        - date_of_birth (date): User's date of birth
        - age_category (text): Calculated age category ('U16', 'U18', 'O18')
        - bank_account_number (text): User's bank account number
        - custom_id (integer): External system identifier (e.g., legacy person_id)
        - email (text): User's email address from auth.users
    
    Example:
        profiles = fetch_profiles(supabase, api_key)
        for profile in profiles:
            print(f"{profile['first_name']} {profile['last_name']} - Email: {profile.get('email')} - Custom ID: {profile.get('custom_id')}")
    """
    try:
        response = supabase.rpc("get_profiles_with_api_key", {
            "p_api_key": api_key
        }).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching profiles: {e}")
        raise


def fetch_work_requests(
    supabase: Client,
    api_key: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Fetch work requests (jobs) for the organization with optional date filtering.
    
    API Function: get_work_requests_with_api_key(
        p_api_key text,
        p_from_date date DEFAULT NULL,
        p_to_date date DEFAULT NULL
    )
    
    Args:
        supabase: Supabase client instance
        api_key: API key for authentication
        from_date: Optional start date (filters by created_at, inclusive)
        to_date: Optional end date (filters by created_at, inclusive)
    
    Returns:
        List of work request dictionaries with fields including:
        - id (uuid): Work request unique identifier
        - requester_id (uuid): ID of user who created the request
        - title (text): Job title
        - description (text): Job description
        - location (text): Job location
        - payment_type (payment_type): 'hourly', 'fixed', 'combination', or 'hourly_per_unit'
        - hourly_rate (numeric): Hourly payment rate
        - fixed_fee (numeric): Fixed payment amount
        - base_fee (numeric): Base payment amount
        - estimated_hours (numeric): Estimated hours to complete
        - desired_start_date (date): Preferred start date
        - status (work_status): 'pending', 'approved', 'assigned', 'in_progress', 'completed', 'cancelled'
        - is_priority (boolean): Whether job is priority
        - needs_coordinator (boolean): Whether job needs a coordinator
        - assigned_to (uuid): ID of assigned worker
        - approved_by (uuid): ID of admin who approved
        - approved_at (timestamp): Approval timestamp
        - created_at (timestamp): Creation timestamp
        - updated_at (timestamp): Last update timestamp
        - organization_id (uuid): Organization identifier
        - is_full (boolean): Whether job has reached capacity
        - contact_person (text): Contact person name
        - completed_at (timestamp): Completion timestamp
        - estimated_u16_workers (integer): Estimated workers under 16
        - estimated_u18_workers (integer): Estimated workers under 18
        - estimated_o18_workers (integer): Estimated workers over 18
        - unit_name (text): Unit name for hourly_per_unit payment type
        - unit_rate (numeric): Rate per unit
        - contact_person_id (uuid): ID of contact person profile
    
    Example:
        # Get all work requests
        requests = fetch_work_requests(supabase, api_key)
        
        # Get work requests from last month
        from_date = date.today() - timedelta(days=30)
        requests = fetch_work_requests(supabase, api_key, from_date=from_date)
    """
    try:
        params = {"p_api_key": api_key}
        
        if from_date is not None:
            params["p_from_date"] = from_date.isoformat()
        if to_date is not None:
            params["p_to_date"] = to_date.isoformat()
        
        response = supabase.rpc("get_work_requests_with_api_key", params).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching work requests: {e}")
        raise


def fetch_job_logs(
    supabase: Client,
    api_key: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Fetch job logs (completed work registrations) with optional date filtering.
    
    API Function: get_job_logs_with_api_key(
        p_api_key text,
        p_from_date date DEFAULT NULL,
        p_to_date date DEFAULT NULL
    )
    
    Args:
        supabase: Supabase client instance
        api_key: API key for authentication
        from_date: Optional start date (filters by date_completed, inclusive)
        to_date: Optional end date (filters by date_completed, inclusive)
    
    Returns:
        List of job log dictionaries with fields including:
        - id (uuid): Job log unique identifier
        - work_request_id (uuid): Associated work request ID (nullable)
        - worker_id (uuid): ID of worker who completed the work
        - work_type (text): Type of work ('snow_removal', 'cleaning', 'gardening', etc.)
        - date_completed (date): Date work was completed
        - hours_worked (numeric): Number of hours worked
        - comments (text): Additional comments
        - rating (integer): Work rating
        - created_at (timestamp): Log creation timestamp
        - organization_id (uuid): Organization identifier
        - work_leader (text): Name of work leader
        - hourly_rate (numeric): Hourly rate for this work
        - reviewed (review_status): Review status ('unreviewed', 'approved', 'denied')
        - worker_first_name (text): Worker's first name
        - worker_last_name (text): Worker's last name
    
    Example:
        # Get all job logs
        logs = fetch_job_logs(supabase, api_key)
        
        # Get job logs for specific date range
        logs = fetch_job_logs(
            supabase, 
            api_key, 
            from_date=date(2025, 1, 1), 
            to_date=date(2025, 1, 31)
        )
    """
    try:
        params = {"p_api_key": api_key}
        
        if from_date is not None:
            params["p_from_date"] = from_date.isoformat()
        if to_date is not None:
            params["p_to_date"] = to_date.isoformat()
        
        response = supabase.rpc("get_job_logs_with_api_key", params).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching job logs: {e}")
        raise


def fetch_job_applications(
    supabase: Client,
    api_key: str,
    work_request_id: str
) -> List[Dict[str, Any]]:
    """
    Fetch job applications for a specific work request.
    
    API Function: get_job_applications_with_api_key(
        p_api_key text,
        p_work_request_id uuid
    )
    
    Args:
        supabase: Supabase client instance
        api_key: API key for authentication
        work_request_id: UUID of the work request
    
    Returns:
        List of job application dictionaries with fields:
        - id (uuid): Application unique identifier
        - work_request_id (uuid): Work request ID
        - user_id (uuid): ID of user who applied
        - created_at (timestamp): Application timestamp
        - user_first_name (text): Applicant's first name
        - user_last_name (text): Applicant's last name
        - user_email (text): Applicant's email address
    
    Example:
        applications = fetch_job_applications(supabase, api_key, "work-request-uuid-here")
        for app in applications:
            print(f"{app['user_first_name']} {app['user_last_name']} applied")
    """
    try:
        response = supabase.rpc("get_job_applications_with_api_key", {
            "p_api_key": api_key,
            "p_work_request_id": work_request_id
        }).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching job applications: {e}")
        raise


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def export_to_csv(data: List[Dict[str, Any]], filename: str):
    """Export data to CSV file."""
    if not data:
        print(f"No data to export to {filename}")
        return
    
    # Get all unique keys from all records
    fieldnames = set()
    for record in data:
        fieldnames.update(record.keys())
    fieldnames = sorted(fieldnames)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            # Convert any non-string values to strings for CSV
            row = {k: str(v) if v is not None else '' for k, v in record.items()}
            writer.writerow(row)
    
    print(f"✓ Exported {len(data)} records to {filename}")


def export_to_json(data: List[Dict[str, Any]], filename: str):
    """Export data to JSON file."""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, default=str, ensure_ascii=False)
    
    print(f"✓ Exported {len(data)} records to {filename}")


def print_summary(data: List[Dict[str, Any]], title: str, show_all: bool = False):
    """Print a summary of the data."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"Total records: {len(data) if data else 0}\n")
    
    if not data:
        print("No records found.")
        return
    
    if show_all:
        # Print all records
        print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    else:
        # Print first record as example
        print("Sample record:")
        print(json.dumps(data[0], indent=2, default=str, ensure_ascii=False))
        
        if len(data) > 1:
            print(f"\n... and {len(data) - 1} more record(s)")


def print_api_documentation():
    """Print API documentation."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMMUNITY ODD JOBS API DOCUMENTATION                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

AUTHENTICATION:
---------------
All API endpoints require an API key. API keys are created by organization admins
through the admin dashboard (Organization Settings > API Key Management).

API keys are passed as the first parameter (p_api_key) to all RPC functions.

ENDPOINTS:
----------

1. get_profiles_with_api_key(p_api_key text)
   Description: Fetches all user profiles for the organization
   Parameters:
     - p_api_key (text, required): API key for authentication
   Returns: Array of profile objects
   Fields returned:
     - id, first_name, last_name, phone, role, availability_notes
     - created_at, updated_at, organization_id, monthly_goal
     - date_of_birth, age_category, bank_account_number, custom_id, email, email

2. get_work_requests_with_api_key(
     p_api_key text,
     p_from_date date DEFAULT NULL,
     p_to_date date DEFAULT NULL
   )
   Description: Fetches work requests (jobs) with optional date filtering
   Parameters:
     - p_api_key (text, required): API key for authentication
     - p_from_date (date, optional): Filter by creation date (inclusive)
     - p_to_date (date, optional): Filter by creation date (inclusive)
   Returns: Array of work request objects
   Note: Date filtering is based on created_at timestamp

3. get_job_logs_with_api_key(
     p_api_key text,
     p_from_date date DEFAULT NULL,
     p_to_date date DEFAULT NULL
   )
   Description: Fetches completed work logs with optional date filtering
   Parameters:
     - p_api_key (text, required): API key for authentication
     - p_from_date (date, optional): Filter by completion date (inclusive)
     - p_to_date (date, optional): Filter by completion date (inclusive)
   Returns: Array of job log objects with worker names
   Note: Date filtering is based on date_completed field

4. get_job_applications_with_api_key(
     p_api_key text,
     p_work_request_id uuid
   )
   Description: Fetches job applications for a specific work request
   Parameters:
     - p_api_key (text, required): API key for authentication
     - p_work_request_id (uuid, required): Work request ID
   Returns: Array of application objects with user information

USAGE EXAMPLES:
---------------

Python (using supabase-py):
    from supabase import create_client
    from datetime import date
    
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # Fetch all profiles
    profiles = supabase.rpc("get_profiles_with_api_key", {
        "p_api_key": "your-api-key"
    }).execute()
    
    # Fetch work requests with date range
    work_requests = supabase.rpc("get_work_requests_with_api_key", {
        "p_api_key": "your-api-key",
        "p_from_date": "2025-01-01",
        "p_to_date": "2025-01-31"
    }).execute()
    
    # Fetch job logs
    job_logs = supabase.rpc("get_job_logs_with_api_key", {
        "p_api_key": "your-api-key",
        "p_from_date": "2025-01-01"
    }).execute()
    
    # Fetch job applications
    applications = supabase.rpc("get_job_applications_with_api_key", {
        "p_api_key": "your-api-key",
        "p_work_request_id": "work-request-uuid"
    }).execute()

ERROR HANDLING:
--------------
All endpoints will raise an exception if:
- Invalid API key is provided
- API key is expired or revoked
- Work request ID doesn't exist (for job applications)
- Work request doesn't belong to the organization (for job applications)

SECURITY:
---------
- API keys are scoped to their organization
- Keys can only access data within their organization
- Keys can be revoked at any time by organization admins
- Keys can have optional expiration dates
- Last used timestamp is tracked for monitoring

""")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Complete API Documentation and Proof of Concept Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show API documentation
  python api_complete_documentation.py --docs
  
  # Fetch all profiles and export to CSV
  python api_complete_documentation.py --profiles --csv
  
  # Fetch work requests from last 7 days, export to JSON
  python api_complete_documentation.py --work-requests --json --from-date 2025-01-01 --to-date 2025-01-07
  
  # Fetch job logs for a date range, export to CSV
  python api_complete_documentation.py --job-logs --csv --from-date 2025-01-01 --to-date 2025-01-31
  
  # Fetch applicants for a work request, export to JSON
  python api_complete_documentation.py --job-applications abc-123-def --json
  
  # Test all endpoints
  python api_complete_documentation.py --all
        """
    )
    
    # Function selection flags
    parser.add_argument("--docs", action="store_true", 
                       help="Show API documentation")
    parser.add_argument("--profiles", action="store_true", 
                       help="Fetch all profiles")
    parser.add_argument("--work-requests", action="store_true", 
                       help="Fetch all work requests")
    parser.add_argument("--job-logs", action="store_true", 
                       help="Fetch job logs")
    parser.add_argument("--job-applications", type=str, metavar="WORK_REQUEST_ID", 
                       help="Fetch job applications for a specific work request")
    parser.add_argument("--all", action="store_true", 
                       help="Test all endpoints")
    
    # Date filtering (for work-requests and job-logs)
    parser.add_argument("--from-date", type=str, metavar="YYYY-MM-DD",
                       help="Start date for filtering (ISO format: YYYY-MM-DD)")
    parser.add_argument("--to-date", type=str, metavar="YYYY-MM-DD",
                       help="End date for filtering (ISO format: YYYY-MM-DD)")
    
    # Output format
    parser.add_argument("--csv", action="store_true", 
                       help="Export results to CSV file")
    parser.add_argument("--json", action="store_true", 
                       help="Export results to JSON file or print as JSON")
    parser.add_argument("--output", type=str, metavar="FILENAME",
                       help="Output filename (default: auto-generated)")
    parser.add_argument("--show-all", action="store_true",
                       help="Show all records instead of just summary")
    
    args = parser.parse_args()
    
    # Show documentation if requested
    if args.docs:
        print_api_documentation()
        return
    
    # Validate configuration
    if not API_KEY or API_KEY == "":
        print("ERROR: API_KEY not set")
        print("\nTo get an API key:")
        print("1. Log in to the admin dashboard")
        print("2. Go to Organization Settings")
        print("3. Create a new API key in the API Key Management section")
        print("\nYou can set API_KEY as an environment variable or update it in this script.")
        return
    
    # Check that at least one function is selected
    function_selected = any([
        args.profiles,
        args.work_requests,
        args.job_logs,
        args.job_applications is not None,
        args.all
    ])
    
    if not function_selected:
        parser.print_help()
        print("\nTip: Use --docs to see API documentation")
        return
    
    # Check output format
    if not args.csv and not args.json:
        args.json = True  # Default to JSON output if nothing specified
    
    # Parse dates if provided
    from_date = None
    to_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid from-date format. Use YYYY-MM-DD (got: {args.from_date})")
            return
    
    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid to-date format. Use YYYY-MM-DD (got: {args.to_date})")
            return
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║              COMMUNITY ODD JOBS API - COMPLETE DOCUMENTATION                 ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\nConnected to: {SUPABASE_URL}")
    print(f"API Key (first 10 chars): {API_KEY[:10]}...")
    
    results = {}
    errors = []
    
    # Process each selected function
    if args.all or args.profiles:
        print("\n" + "="*80)
        print("Fetching PROFILES...")
        print("="*80)
        try:
            data = fetch_profiles(supabase, API_KEY)
            results['profiles'] = data
            
            if args.csv:
                filename = args.output or f"profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_to_csv(data, filename)
            elif args.json and args.output:
                export_to_json(data, args.output)
            else:
                print_summary(data, "Profiles", args.show_all)
        except Exception as e:
            error_msg = f"Failed to fetch profiles: {e}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)
    
    if args.all or args.work_requests:
        print("\n" + "="*80)
        print("Fetching WORK REQUESTS...")
        if from_date or to_date:
            print(f"Date filter: {from_date or 'no start'} to {to_date or 'no end'}")
        print("="*80)
        try:
            data = fetch_work_requests(supabase, API_KEY, from_date, to_date)
            results['work_requests'] = data
            
            if args.csv:
                filename = args.output or f"work_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_to_csv(data, filename)
            elif args.json and args.output:
                export_to_json(data, args.output)
            else:
                print_summary(data, "Work Requests", args.show_all)
        except Exception as e:
            error_msg = f"Failed to fetch work requests: {e}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)
    
    if args.all or args.job_logs:
        print("\n" + "="*80)
        print("Fetching JOB LOGS...")
        if from_date or to_date:
            print(f"Date filter: {from_date or 'no start'} to {to_date or 'no end'}")
        print("="*80)
        try:
            data = fetch_job_logs(supabase, API_KEY, from_date, to_date)
            results['job_logs'] = data
            
            if args.csv:
                filename = args.output or f"job_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_to_csv(data, filename)
            elif args.json and args.output:
                export_to_json(data, args.output)
            else:
                print_summary(data, "Job Logs", args.show_all)
        except Exception as e:
            error_msg = f"Failed to fetch job logs: {e}"
            print(f"ERROR: {error_msg}")
            errors.append(error_msg)
    
    if args.all or args.job_applications:
        if args.job_applications:
            print("\n" + "="*80)
            print(f"Fetching JOB APPLICATIONS for work request: {args.job_applications}")
            print("="*80)
            try:
                data = fetch_job_applications(supabase, API_KEY, args.job_applications)
                results['job_applications'] = data
                
                if args.csv:
                    filename = args.output or f"job_applications_{args.job_applications}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    export_to_csv(data, filename)
                elif args.json and args.output:
                    export_to_json(data, args.output)
                else:
                    print_summary(data, f"Job Applications (Work Request: {args.job_applications})", args.show_all)
            except Exception as e:
                error_msg = f"Failed to fetch job applications: {e}"
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)
        elif args.all:
            print("\n" + "="*80)
            print("Skipping JOB APPLICATIONS (requires --job-applications <work_request_id>)")
            print("="*80)
    
    # If multiple functions were called and JSON output requested, print combined results
    if len(results) > 1 and args.json and not args.output:
        print("\n" + "="*80)
        print("COMBINED RESULTS")
        print("="*80)
        print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for key, data in results.items():
        print(f"  {key}: {len(data)} records")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    
    print("\n" + "="*80)
    print("Test completed!")
    print("="*80)
    print("\nFor API documentation, run: python api_complete_documentation.py --docs")


if __name__ == "__main__":
    main()

