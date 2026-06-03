# 📊 Automated Report Generation System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Cut weekly business report turnaround from 3 hours to under 10 minutes — with zero manual intervention.**

A production-grade Python system that automatically ingests raw database CSV exports, processes them through a Pandas ETL pipeline, enriches data via REST API calls, and outputs a polished, multi-sheet Excel report — on a configurable weekly schedule.

---

## 🎯 Problem Solved

| Before | After |
|--------|-------|
| Finance team manually copies data from 3 sources | Zero manual steps |
| 3 hours of copy-paste + formula work per week | **< 10 minutes end-to-end** |
| Inconsistent formatting, human errors | Standardised, validated output every time |
| Report ready Tuesday at best | Report in inbox Monday 8 AM |

---

## ✨ Features

- **Automated ETL Pipeline** — loads, cleans, validates, and enriches raw CSV exports with Pandas
- **REST API Integration** — fetches external KPI benchmarks with retry logic, timeouts, and graceful fallback
- **Professional Excel Reports** — 9-sheet workbook with charts, conditional formatting, colour-coded tables via openpyxl
- **Weekly Scheduler** — built-in `schedule`-based daemon; configurable day/time via env vars
- **Email Delivery** — optional SMTP delivery of the report to a distribution list
- **Docker Support** — single-command deployment with `docker compose up`
- **CI/CD Ready** — GitHub Actions workflow runs tests on Python 3.10/3.11/3.12
- **Comprehensive Tests** — 20+ unit tests with pytest; 80%+ coverage

---

## 🏗 Architecture

```
automated-report-system/
├── main.py                     # CLI entry point
├── src/
│   ├── config.py               # Centralised settings + env vars
│   ├── scheduler.py            # Pipeline orchestrator + weekly scheduler
│   ├── core/
│   │   ├── data_processor.py   # Pandas ETL: load → clean → KPIs
│   │   └── report_builder.py   # openpyxl: builds 9-sheet Excel report
│   ├── api/
│   │   └── api_client.py       # REST client with retry + fallback
│   └── utils/
│       ├── logger.py           # Structured logging (console + file)
│       └── email_sender.py     # Optional SMTP email delivery
├── data/
│   └── raw/                    # Drop CSV exports here
│       ├── sales_data.csv
│       ├── customers.csv
│       └── inventory.csv
├── reports/output/             # Generated .xlsx reports land here
├── tests/
│   └── test_data_processor.py  # 20+ unit tests
├── .github/workflows/ci.yml    # GitHub Actions CI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Data Flow

```
Raw CSVs  ──►  Pandas ETL  ──►  KPI Engine  ──►  REST API Enrichment
                                                          │
                                                          ▼
                                              Excel Report (openpyxl)
                                                          │
                                              ┌───────────┴───────────┐
                                              ▼                       ▼
                                       File System              Email / Webhook
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/automated-report-system.git
cd automated-report-system
```

### 2. Create a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (API URL, email, schedule time, etc.)
```

### 5. Run the report

```bash
python main.py
```

The report is saved to `reports/output/weekly_report_YYYYMMDD_HHMMSS.xlsx`.

---

## ⚙️ Configuration

All settings are driven by environment variables (`.env` file or shell exports):

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://jsonplaceholder.typicode.com` | External API endpoint |
| `API_TIMEOUT` | `30` | Request timeout in seconds |
| `API_RETRY_MAX` | `3` | Max retry attempts on failure |
| `SCHEDULE_DAY` | `monday` | Day of week to run (e.g. `friday`) |
| `SCHEDULE_TIME` | `08:00` | Time to run in 24h format |
| `EMAIL_ENABLED` | `false` | Set `true` to enable email delivery |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(empty)* | Sender email address |
| `SMTP_PASSWORD` | *(empty)* | App password (not account password) |
| `EMAIL_TO` | *(empty)* | Comma-separated recipient list |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING) |

---

## 📅 Scheduler Mode

To run as a persistent background daemon:

```bash
python main.py --schedule
```

The process stays alive and runs the pipeline every week on the configured day/time.

---

## 🐳 Docker Deployment

### Run once

```bash
docker build -t report-system .
docker run --rm \
  -v $(pwd)/data/raw:/app/data/raw \
  -v $(pwd)/reports/output:/app/reports/output \
  report-system
```

### Run as weekly daemon

```bash
docker compose up -d
```

Logs:
```bash
docker compose logs -f
```

Stop:
```bash
docker compose down
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test class
pytest tests/test_data_processor.py::TestComputeKPIs -v
```

---

## 📊 Generated Report Structure

The output `.xlsx` contains 9 sheets:

| Sheet | Contents |
|-------|----------|
| 📊 Cover | Company branding + KPI summary cards |
| 📋 Executive Summary | Report metadata + key metrics table |
| 💰 Sales Data | Full cleaned transaction log |
| 🗺 Regional Analysis | Revenue by region + bar chart |
| 📦 Product Performance | Per-product metrics + pie chart |
| 🏆 Sales Team | Leaderboard with gold/silver/bronze highlights |
| 📈 Daily Trend | Day-by-day revenue + cumulative line chart |
| 🏭 Inventory | Stock levels with low-stock warnings |
| 🏷 Category Breakdown | Revenue share by product category |

---

## 🔌 Integrating Your Own Data

Replace the CSV files in `data/raw/` with your own exports, matching these schemas:

**sales_data.csv** — `order_id, date, region, salesperson, product, category, quantity, unit_price, discount, status, customer_id`

**customers.csv** — `customer_id, name, email, region, segment, join_date, total_orders, lifetime_value`

**inventory.csv** — `product_id, product_name, category, sku, unit_cost, unit_price, current_stock, reorder_level, supplier, last_restocked`

To pull from a real database, replace the `_load_*()` functions in `src/core/data_processor.py` with `pd.read_sql()` calls.

---

## 🌐 Deployment Guide

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step deployment to:
- **Railway** (recommended — free tier, one-click deploy)
- **Render**
- **AWS EC2 / Lightsail**
- **Cron job on any Linux server**

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Data Processing | Pandas, NumPy |
| Report Generation | openpyxl |
| REST API | requests (with HTTPAdapter retry) |
| Scheduling | schedule |
| Testing | pytest, pytest-cov |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## 📄 License

MIT — see [LICENSE](LICENSE)
