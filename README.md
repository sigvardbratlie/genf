# GENF

A uv workspace with multiple Streamlit-based tools for the GENF organization.

## Modules

This repo is structured as a uv workspace with the following modules:

### 📊 [Dashboard](dashboard/)
A comprehensive analytics tool for managing and tracking GENF activities, hours, compensation, and member performance.

**Features:**
- Hours and compensation tracking
- Season-based review
- Annual summary
- Member management
- Integration with BigQuery and Supabase

### 🏆 [Contest](contest/)
An application for managing and conducting contests within GENF.

### 📋 [Survey](survey/)
Tools for handling surveys and analyzing results.

## Getting Started

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) installed

### Installation

1. Clone the repo:
```bash
git clone <repository-url>
cd genf
```

2. Install dependencies for the entire workspace:
```bash
uv sync
```

Or for a specific module:
```bash
cd dashboard
uv sync
```

### Running modules

Each module has its own README with specific instructions. See:
- [Dashboard README](dashboard/README.md)
- [Contest README](contest/README.md)
- [Survey README](survey/README.md)

## Project Structure

```
genf/
├── dashboard/          # Main analytics dashboard
├── survey/             # Surveys
├── pyproject.toml      # Workspace configuration
└── README.md           # This file
```

## Technology Stack

- **Frontend**: Streamlit
- **Data Warehouse**: Google Cloud BigQuery
- **Database**: Supabase
- **Visualization**: Plotly, Seaborn, Matplotlib
- **Data Processing**: Pandas, NumPy
- **Package Management**: uv

---
*An internal tool for the GENF organization.*
