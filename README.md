# Wannabe Google

A highly scalable typeahead search system featuring exact-prefix matching, consistent hashing load balancing, batch-write optimization, and time-decayed trending scores. 

## System Flow

![Architecture Flow](https://mermaid.ink/img/eyJjb2RlIjogImdyYXBoIExSXG4gICAgQ2xpZW50W1JlYWN0IFVJXSAtLT4gQVBJW0Zhc3RBUEldXG4gICAgQVBJIC0tPiBIYXNoW0NvbnNpc3RlbnQgSGFzaCBSaW5nXVxuICAgIEhhc2ggLS0-IFIxW1JlZGlzIDFdXG4gICAgSGFzaCAtLT4gUjJbUmVkaXMgMl1cbiAgICBIYXNoIC0tPiBSM1tSZWRpcyAzXVxuICAgIEFQSSAtLT58QmF0Y2ggV3JpdGVzfCBEQlsoUG9zdGdyZVNRTCldXG4iLCAibWVybWFpZCI6IHsidGhlbWUiOiAiZGVmYXVsdCJ9fQ==)

## Local Setup Instructions

### 1. Configure Environment Variables
Before starting the infrastructure or the backend, you must configure your environment variables by copying the example file:
```bash
cd Backend
cp .env.example .env
```

### 2. Start the Infrastructure
We use Docker to run the primary PostgreSQL database and 3 distributed Redis nodes.
```bash
cd Backend
docker-compose up -d
```

### 3. Run the Backend API
```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt greenlet
uvicorn app.main:app --reload
```

### 4. Seed the Data (One-time)
Populate the database with 20,000 queries from the AOL dataset:
```bash
cd Backend
source venv/bin/activate
python seed_data.py
```

### 5. Run the Frontend
```bash
cd Frontend
npm install
npm run dev
```
