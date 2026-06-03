FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p reports/output data/processed data/exports logs

ENV PYTHONUNBUFFERED=1

# Railway sets PORT automatically — we just expose and read it at runtime
EXPOSE $PORT

CMD python main.py --web --schedule
