# GENF Dashboard

A comprehensive Streamlit-based analytics dashboard for managing and tracking GENF organization activities, hours, compensation, and member performance.

## Overview

The GENF Dashboard provides real-time insights into organizational operations across multiple seasons, enabling administrators to monitor hours worked, costs, member engagement, and goal achievement.

## Features

### ⏰ Hours and Compensation Tracking
- Monitor total hours worked and associated costs per period
- Filter by name, role, group, and project
- View cumulative salary trends across seasons
- Export data to CSV or Excel format
- Historical data tracking across multiple fiscal years


### 📊 Review
- Seasonal & annual review

### 💰 Buk.cash Integration
- Financial data integration from Buk.cash platform
- Job logs and transaction tracking with date filtering

## Technology Stack

- **Frontend**: Streamlit
- **Data Warehouse**: Google Cloud BigQuery
- **Database**: Supabase
- **Visualization**: Plotly, Seaborn, Matplotlib
- **Data Processing**: Pandas, NumPy
- **Authentication**: Google OAuth2, Authlib

## Installation

1. Navigate to the dashboard folder:
```bash
cd dashboard
```

2. Install dependencies:
```bash
uv sync
```

3. Configure secrets in `.streamlit/secrets.toml`:
```toml
[gcp_service_account]
# Google Cloud service account credentials

[supabase]
SUPABASE_URL = "your-supabase-url"
SUPABASE_ANON_KEY = "your-anon-key"
API_KEY = "your-api-key"
```

## Usage

Run the dashboard:
```bash
streamlit run main.py
```

Navigate to `http://localhost:8501` in your browser.

## Project Structure

```
dashboard/
├── main.py                    # Main dashboard homepage
├── utilities.py               # Shared utility functions and database queries
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Package configuration
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   └── secrets.toml          # API keys and credentials (not in version control)
├── pages/
│   ├── timer.py              # Hours and salary tracking page
│   ├── seasonal_review.py    # Seasonal performance analysis
│   ├── yearly_review.py      # Annual review page
│   ├── members.py            # Member management page
│   └── buk_cash.py           # Buk.cash integration page
├── components/               # Reusable UI components
└── tests/                    # Tests
```

## Data Schema

### Roles

- **GEN-F**: Primary youth program participants
- **Hjelpementor**: Assistant mentors
- **Mentor**: Senior mentors

### Seasons

Data is organized by fiscal seasons (August to July):
- 25/26 (2025-2026)
- 24/25 (2024-2025)
- 23/24 (2023-2024)
- 22/23 (2022-2023)

## Key Functionality

### Date Filtering
- Predefined date ranges (last 1-4 months)
- Season-based filtering
- Custom date range selection

### Data Caching
- BigQuery results cached for 1 hour (TTL: 3600s)
- Buk.cash job logs cached for 10 minutes (TTL: 600s)

### Export Options
- CSV export for data analysis
- Excel export with formatting support

## Contributing

When contributing to this repository, please ensure:
1. Code follows existing patterns in `utilities.py`
2. New pages include proper initialization via `init()` and `sidebar_setup()`
3. Data queries use the cached `run_query()` function
4. All sensitive credentials remain in `secrets.toml`

## License

[Specify your license here]

---
*Internal tool for the GENF organization.*
