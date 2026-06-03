# 🚀 Deployment Guide

This guide covers deploying the Automated Report System to several platforms. **Railway is recommended** for beginners — it's free, requires no credit card, and deploys in under 5 minutes.

---

## Option 1: Railway (Recommended — Free Tier)

Railway runs your Docker container on a persistent server and supports environment variables natively.

### Steps

1. **Create a Railway account**
   - Go to [railway.app](https://railway.app) and sign up with GitHub.

2. **Push your project to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/automated-report-system.git
   git push -u origin main
   ```

3. **Create a new Railway project**
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your `automated-report-system` repository
   - Railway auto-detects the `Dockerfile` and starts building

4. **Set environment variables**
   - In the Railway dashboard, go to your service → **Variables** tab
   - Add each variable from `.env.example`:
     ```
     SCHEDULE_DAY=monday
     SCHEDULE_TIME=08:00
     LOG_LEVEL=INFO
     ```
   - If using email, also add `EMAIL_ENABLED`, `SMTP_USER`, etc.

5. **Override the start command to use scheduler mode**
   - In Railway → Service Settings → **Start Command**:
     ```
     python main.py --schedule
     ```

6. **Deploy**
   - Click **Deploy** — Railway builds the Docker image and starts the container
   - Your scheduler is now running 24/7

7. **View logs**
   - Click your service → **Logs** tab to see the pipeline output

8. **Persistent storage for reports**
   - Railway volumes let you persist the `reports/output/` directory
   - Go to **Volumes** → Add Volume → mount at `/app/reports/output`

---

## Option 2: Render (Free Tier)

1. Go to [render.com](https://render.com) and sign up.
2. Click **New** → **Web Service** → connect your GitHub repo.
3. Set:
   - **Environment**: Docker
   - **Start Command**: `python main.py --schedule`
4. Add environment variables in the **Environment** tab.
5. Click **Create Web Service**.

> ⚠️ Render's free tier spins down after 15 minutes of inactivity — use a paid plan ($7/mo) or Railway for a persistent scheduler.

---

## Option 3: AWS EC2 / Lightsail (Production)

### a) Launch an instance

- Go to [AWS Lightsail](https://lightsail.aws.amazon.com)
- Create instance → Linux/Unix → OS Only → Ubuntu 22.04
- Choose $3.50/mo (1GB RAM is enough)
- Add your SSH key

### b) SSH in and install Docker

```bash
ssh ubuntu@YOUR_INSTANCE_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker
```

### c) Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/automated-report-system.git
cd automated-report-system
cp .env.example .env
nano .env    # fill in your values
```

### d) Run with Docker Compose

```bash
docker compose up -d
docker compose logs -f
```

The scheduler runs inside Docker, restarting automatically on crashes.

### e) Retrieve generated reports

Use SCP to download reports:
```bash
scp ubuntu@YOUR_IP:/home/ubuntu/automated-report-system/reports/output/*.xlsx ./
```

Or mount an S3 bucket using `s3fs` for automatic upload.

---

## Option 4: Linux Server with cron (Simplest)

If you just want to run the pipeline on a schedule without Docker:

### a) Install on the server

```bash
git clone https://github.com/YOUR_USERNAME/automated-report-system.git
cd automated-report-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env
```

### b) Add a cron job

```bash
crontab -e
```

Add this line to run every Monday at 8 AM:
```cron
0 8 * * 1 cd /home/ubuntu/automated-report-system && /home/ubuntu/automated-report-system/venv/bin/python main.py >> logs/cron.log 2>&1
```

### c) Verify the cron job

```bash
crontab -l
```

---

## Option 5: GitHub Actions (Run on Schedule in CI)

You can run the report pipeline on a schedule entirely within GitHub Actions — no server needed. Reports are uploaded as build artifacts.

Create `.github/workflows/weekly-report.yml`:

```yaml
name: Weekly Report

on:
  schedule:
    - cron: '0 8 * * 1'   # Every Monday at 08:00 UTC
  workflow_dispatch:        # Allow manual trigger

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run report pipeline
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
        run: python main.py

      - name: Upload report artifact
        uses: actions/upload-artifact@v4
        with:
          name: weekly-report
          path: reports/output/*.xlsx
          retention-days: 30
```

**Steps:**
1. Add any secrets (API keys etc.) under **Settings → Secrets → Actions**
2. Push this workflow file
3. The report runs automatically every Monday and is downloadable from the Actions tab

---

## Connecting to a Real Database

Replace CSV loading with a database connection:

### PostgreSQL / MySQL

```bash
pip install sqlalchemy psycopg2-binary   # or pymysql
```

In `src/core/data_processor.py`, replace `_load_sales()`:

```python
from sqlalchemy import create_engine

def _load_sales() -> pd.DataFrame:
    engine = create_engine(os.getenv("DATABASE_URL"))
    return pd.read_sql(
        "SELECT * FROM orders WHERE date >= NOW() - INTERVAL '7 days'",
        engine,
        parse_dates=["date"],
    )
```

Set `DATABASE_URL=postgresql://user:pass@host:5432/dbname` in your `.env`.

---

## Uploading Reports to Cloud Storage

### Google Drive (via Google Sheets API)

```bash
pip install google-api-python-client google-auth
```

### AWS S3

```bash
pip install boto3
```

```python
import boto3

def upload_to_s3(local_path: str, bucket: str, key: str):
    s3 = boto3.client("s3")
    s3.upload_file(local_path, bucket, key)
    print(f"Uploaded to s3://{bucket}/{key}")
```

Add a call to `upload_to_s3()` at the end of `run_pipeline()` in `src/scheduler.py`.

---

## Summary

| Platform | Cost | Difficulty | Best For |
|----------|------|-----------|----------|
| Railway | Free / $5/mo | ⭐ Easy | Demo, learning, small teams |
| Render | Free / $7/mo | ⭐ Easy | Similar to Railway |
| GitHub Actions | Free (2000 min/mo) | ⭐⭐ Medium | Serverless, report-as-artifact |
| AWS Lightsail | $3.50/mo | ⭐⭐ Medium | Production, full control |
| Linux + cron | Server cost | ⭐ Easy | Existing server |
