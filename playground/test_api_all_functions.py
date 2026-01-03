#!/usr/bin/env python3
"""
Proof of Concept: Test all API functions with CSV/JSON export
Demonstrates all available API key functions:
- get_profiles_with_api_key
- get_work_requests_with_api_key
- get_job_logs_with_api_key
- get_job_applications_with_api_key

Requirements:
    pip install supabase

Usage:
    python test_api_all_functions.py --profiles --json
    python test_api_all_functions.py --work-requests --csv --from-date 2025-01-01
    python test_api_all_functions.py --job-logs --csv --from-date 2025-01-01 --to-date 2025-01-31
    python test_api_all_functions.py --job-applications <work_request_id> --json
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
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install supabase")
    sys.exit(1)

# Configuration - Update these with your credentials
SUPABASE_URL = "https://qvkdyodpfauvpsamrmew.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2a2R5b2RwZmF1dnBzYW1ybWV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzNzMyMDEsImV4cCI6MjA2NDk0OTIwMX0.gMscCXj733-_cT87_ErXPHaaa3YQdWE5gjpJ8XZ4yXI"
API_KEY = ""


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


def print_json(data: List[Dict[str, Any]], title: str):
    """Print data as formatted JSON."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"Total records: {len(data) if data else 0}\n")
    
    if not data:
        print("No records found.")
        return
    
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def print_summary(data: List[Dict[str, Any]], title: str):
    """Print a summary of the data."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"Total records: {len(data) if data else 0}\n")
    
    if not data:
        print("No records found.")
        return
    
    # Print first record as example
    print("Sample record:")
    print(json.dumps(data[0], indent=2, default=str, ensure_ascii=False))
    
    if len(data) > 1:
        print(f"\n... and {len(data) - 1} more record(s)")


def fetch_profiles(supabase: Client, api_key: str) -> List[Dict[str, Any]]:
    """Fetch all profiles using API key."""
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
    """Fetch work requests using API key with optional date filtering."""
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
    """Fetch job logs using API key with optional date filtering."""
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
    """Fetch job applications for a specific work request."""
    try:
        response = supabase.rpc("get_job_applications_with_api_key", {
            "p_api_key": api_key,
            "p_work_request_id": work_request_id
        }).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching job applications: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Test all Supabase API functions with CSV/JSON export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get all profiles and export to CSV
  python test_api_all_functions.py --profiles --csv
  
  # Get work requests from last 7 days, export to JSON
  python test_api_all_functions.py --work-requests --json --from-date 2025-01-01 --to-date 2025-01-07
  
  # Get job logs for a date range, export to CSV
  python test_api_all_functions.py --job-logs --csv --from-date 2025-01-01 --to-date 2025-01-31
  
  # Get applicants for a work request, export to JSON
  python test_api_all_functions.py --job-applications abc-123-def --json
        """
    )
    
    # Function selection flags
    parser.add_argument("--profiles", action="store_true", help="Fetch all profiles")
    parser.add_argument("--work-requests", action="store_true", help="Fetch all work requests")
    parser.add_argument("--job-logs", action="store_true", help="Fetch job logs")
    parser.add_argument("--job-applications", type=str, metavar="WORK_REQUEST_ID", 
                       help="Fetch job applications for a specific work request (requires work request ID)")
    
    # Date filtering (for work-requests and job-logs)
    parser.add_argument("--from-date", type=str, metavar="YYYY-MM-DD",
                       help="Start date for filtering (ISO format: YYYY-MM-DD)")
    parser.add_argument("--to-date", type=str, metavar="YYYY-MM-DD",
                       help="End date for filtering (ISO format: YYYY-MM-DD)")
    
    # Output format
    parser.add_argument("--csv", action="store_true", help="Export results to CSV file")
    parser.add_argument("--json", action="store_true", help="Export results to JSON file or print as JSON")
    parser.add_argument("--output", type=str, metavar="FILENAME",
                       help="Output filename (default: auto-generated based on function and format)")
    
    args = parser.parse_args()
    
    # Validate configuration
    if not API_KEY or API_KEY == "":
        print("WARNING: Please set API_KEY in the script")
        print("\nTo get an API key:")
        print("1. Log in to the admin dashboard")
        print("2. Go to Organization Settings")
        print("3. Create a new API key in the API Key Management section")
        return
    
    # Check that at least one function is selected
    function_selected = any([
        args.profiles,
        args.work_requests,
        args.job_logs,
        args.job_applications is not None
    ])
    
    if not function_selected:
        parser.print_help()
        print("\nError: Please select at least one function to test (--profiles, --work-requests, --job-logs, or --job-applications)")
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
    
    print("Supabase API Functions Test")
    print("=" * 80)
    print(f"Connected to: {SUPABASE_URL}")
    print(f"API Key (first 10 chars): {API_KEY[:10]}...")
    
    # Process each selected function
    results = {}
    
    if args.profiles:
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
                print_summary(data, "Profiles")
        except Exception as e:
            print(f"Failed to fetch profiles: {e}")
    
    if args.work_requests:
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
                print_summary(data, "Work Requests")
        except Exception as e:
            print(f"Failed to fetch work requests: {e}")
    
    if args.job_logs:
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
                print_summary(data, "Job Logs")
        except Exception as e:
            print(f"Failed to fetch job logs: {e}")
    
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
                print_summary(data, f"Job Applications (Work Request: {args.job_applications})")
        except Exception as e:
            print(f"Failed to fetch job applications: {e}")
    
    # If multiple functions were called and JSON output requested, print combined results
    if len(results) > 1 and args.json and not args.output:
        print("\n" + "="*80)
        print("COMBINED RESULTS")
        print("="*80)
        print_json(results, "All Results")
    
    print("\n" + "="*80)
    print("Test completed!")
    print("="*80)


if __name__ == "__main__":
    main()

