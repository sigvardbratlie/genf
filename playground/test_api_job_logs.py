#!/usr/bin/env python3
"""
Proof of Concept: Query work registrations (job logs) via API key

This script demonstrates how to use the Supabase API to fetch work registrations
using an API key with optional date filtering.

Requirements:
    pip install supabase python-dotenv

Usage:
    1. Set environment variables or update the constants below:
       - SUPABASE_URL
       - SUPABASE_ANON_KEY
       - API_KEY
    
    2. Run: python test_api_job_logs.py
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional
import json

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install supabase python-dotenv")
    exit(1)

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration - Update these or set as environment variables
# Project ID: qvkdyodpfauvpsamrmew
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qvkdyodpfauvpsamrmew.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2a2R5b2RwZmF1dnBzYW1ybWV3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzNzMyMDEsImV4cCI6MjA2NDk0OTIwMX0.gMscCXj733-_cT87_ErXPHaaa3YQdWE5gjpJ8XZ4yXI")
API_KEY = os.getenv("API_KEY", "07c78e44a658705dfde241ba2cd239d9")


def get_date_range(period: str) -> tuple[Optional[date], Optional[date]]:
    """
    Calculate date range for common periods.
    
    Args:
        period: One of 'last_week', 'last_month', 'last_year', 'all'
    
    Returns:
        Tuple of (from_date, to_date). Both can be None for 'all'.
    """
    today = date.today()
    
    if period == "last_week":
        from_date = today - timedelta(days=7)
        return (from_date, today)
    elif period == "last_month":
        from_date = today - timedelta(days=30)
        return (from_date, today)
    elif period == "last_year":
        from_date = today - timedelta(days=365)
        return (from_date, today)
    elif period == "all":
        return (None, None)
    else:
        raise ValueError(f"Unknown period: {period}")


def fetch_job_logs(
    supabase: Client,
    api_key: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> list[dict]:
    """
    Fetch job logs using API key with optional date filtering.
    
    Args:
        supabase: Supabase client instance
        api_key: API key for authentication
        from_date: Optional start date (inclusive)
        to_date: Optional end date (inclusive)
    
    Returns:
        List of job log records
    """
    # Prepare parameters for the RPC call
    # Only include date parameters if they are provided (not None)
    params = {"p_api_key": api_key}
    
    if from_date is not None:
        params["p_from_date"] = from_date.isoformat()
    if to_date is not None:
        params["p_to_date"] = to_date.isoformat()
    
    try:
        # Call the RPC function
        response = supabase.rpc("get_job_logs_with_api_key", params).execute()
        
        if response.data is None:
            return []
        
        return response.data
    
    except Exception as e:
        print(f"Error fetching job logs: {e}")
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        raise


def print_results(logs: list[dict], title: str):
    """Print job logs in a readable format."""
    try:
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
        print(f"Total records: {len(logs) if logs else 0}\n")
        
        if not logs:
            print("No records found.")
            return
        
        # Print all records (or first 10 as examples if there are many)
        max_display = min(len(logs), 10)
        for i, log in enumerate(logs[:max_display], 1):
            try:
                print(f"Record {i}:")
                print(f"  ID: {log.get('id')}")
                print(f"  Worker ID: {log.get('worker_id')}")
                print(f"  Work Type: {log.get('work_type')}")
                print(f"  Date Completed: {log.get('date_completed')}")
                print(f"  Hours Worked: {log.get('hours_worked')}")
                print(f"  Hourly Rate: {log.get('hourly_rate')}")
                work_leader = log.get('work_leader')
                print(f"  Work Leader: {work_leader if work_leader else 'None'}")
                print(f"  Reviewed: {log.get('reviewed')}")
                comments = log.get('comments')
                if comments:
                    comments_display = comments[:50] + "..." if len(comments) > 50 else comments
                else:
                    comments_display = "N/A"
                print(f"  Comments: {comments_display}")
                print()
            except Exception as e:
                print(f"  Error printing record {i}: {e}")
                print(f"  Record data: {log}")
                print()
        
        if len(logs) > max_display:
            print(f"... and {len(logs) - max_display} more records\n")
        
        # Only print JSON if we have records
        if logs and len(logs) > 0:
            print(f"Full JSON (first record):")
            print(json.dumps(logs[0], indent=2, default=str))
    except Exception as e:
        print(f"Error in print_results: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function demonstrating various API usage patterns."""
    
    print("Supabase API Key Test - Job Logs Query")
    print("=" * 80)
    
    # Validate configuration
    if "your-project" in SUPABASE_URL or SUPABASE_ANON_KEY == "your-anon-key-here":
        print("WARNING: Please update SUPABASE_URL and SUPABASE_ANON_KEY in the script or .env file")
        return
    
    if API_KEY == "your-api-key-here" or not API_KEY:
        print("WARNING: Please update API_KEY in the script or .env file")
        print("\nTo get an API key:")
        print("1. Log in to the admin dashboard")
        print("2. Go to Organization Settings")
        print("3. Create a new API key in the API Key Management section")
        return
    
    # Initialize Supabase client
    # Note: The API key is passed as a parameter to the RPC function, not in headers
    # The Supabase client uses the anon key for authentication
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    print(f"Connected to: {SUPABASE_URL}")
    print(f"API Key (first 10 chars): {API_KEY[:10]}...")
    
    # Example 1: Fetch all job logs
    print("\n" + "="*80)
    print("Example 1: Fetching ALL job logs (no date filter)")
    print("="*80)
    try:
        all_logs = fetch_job_logs(supabase, API_KEY)
        print_results(all_logs, "All Job Logs")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Example 2: Fetch logs from last week
    print("\n" + "="*80)
    print("Example 2: Fetching job logs from LAST WEEK")
    print("="*80)
    try:
        from_date, to_date = get_date_range("last_week")
        print(f"Date range: {from_date} to {to_date}")
        week_logs = fetch_job_logs(supabase, API_KEY, from_date, to_date)
        print_results(week_logs, f"Job Logs (Last Week: {from_date} to {to_date})")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Example 3: Fetch logs from last month
    print("\n" + "="*80)
    print("Example 3: Fetching job logs from LAST MONTH")
    print("="*80)
    try:
        from_date, to_date = get_date_range("last_month")
        print(f"Date range: {from_date} to {to_date}")
        month_logs = fetch_job_logs(supabase, API_KEY, from_date, to_date)
        print_results(month_logs, f"Job Logs (Last Month: {from_date} to {to_date})")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Example 4: Fetch logs from last year
    print("\n" + "="*80)
    print("Example 4: Fetching job logs from LAST YEAR")
    print("="*80)
    try:
        from_date, to_date = get_date_range("last_year")
        print(f"Date range: {from_date} to {to_date}")
        year_logs = fetch_job_logs(supabase, API_KEY, from_date, to_date)
        print_results(year_logs, f"Job Logs (Last Year: {from_date} to {to_date})")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Example 5: Custom date range
    print("\n" + "="*80)
    print("Example 5: Fetching job logs for CUSTOM DATE RANGE")
    print("="*80)
    try:
        # Example: Last 3 months
        custom_from = date.today() - timedelta(days=90)
        custom_to = date.today()
        print(f"Date range: {custom_from} to {custom_to}")
        custom_logs = fetch_job_logs(supabase, API_KEY, custom_from, custom_to)
        print_results(custom_logs, f"Job Logs (Custom Range: {custom_from} to {custom_to})")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Example 6: Only from_date (all records from a certain date onwards)
    print("\n" + "="*80)
    print("Example 6: Fetching job logs FROM a specific date (no end date)")
    print("="*80)
    try:
        from_date_only = date.today() - timedelta(days=14)
        print(f"From date: {from_date_only} (no end date)")
        from_only_logs = fetch_job_logs(supabase, API_KEY, from_date=from_date_only)
        print_results(from_only_logs, f"Job Logs (From {from_date_only} onwards)")
    except Exception as e:
        print(f"Failed: {e}")
    
    print("\n" + "="*80)
    print("Test completed!")
    print("="*80)


if __name__ == "__main__":
    main()

