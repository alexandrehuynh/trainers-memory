# Trainer's Memory Setup Guide

This document provides instructions for setting up and running the Trainer's Memory application.

## Prerequisites

- Python 3.10+ (recommended)
- Node.js 16+ (required for frontend)
- PostgreSQL database
- Redis (optional but recommended for caching)

## Backend Setup

1. **Create a virtual environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `OPENAI_API_KEY`: Your OpenAI API key (if using AI features)
- `REDIS_URL`: Redis connection URL (optional for caching)

4. **Initialize the database**

```bash
alembic upgrade head
```

5. **Generate a test API key**

```bash
./scripts/generate_api_key.py
```
This will create a test client and API key in the database. Save the output API key for testing.

6. **Start the development server**

```bash
./scripts/start_dev.sh
```

This script will:
- Check if Redis is running and attempt to start it if not
- Ensure your .env file exists
- Start the FastAPI server with hot reloading

## Frontend Setup

1. **Install dependencies**

```bash
cd src
npm install
```

2. **Start the development server**

```bash
npm run dev
```

## API Authentication

The API uses API key authentication. Include the API key in the `X-API-Key` header with each request:

```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/api/v1/me
```

For testing the Swagger UI docs, click the "Authorize" button and enter your API key.

## Troubleshooting

### Redis Connection Errors

If you see "Redis cache for OpenAI failed to connect - caching disabled", it means Redis is not running. 
The application will still work but without caching OpenAI responses.

To fix:
- Install Redis: `brew install redis` (on Mac)
- Start Redis: `brew services start redis`

### API 401 Unauthorized Errors

If you receive 401 errors when testing the API:
1. Ensure you've generated an API key using the script
2. Include the API key in the `X-API-Key` header
3. For the Swagger docs, click "Authorize" and enter your API key

### Frontend Punycode Warnings

The "punycode module is deprecated" warning is a Node.js deprecation warning and doesn't affect functionality.
We've added a `.npmrc` file to suppress these warnings.

### Database Connection Issues

If you encounter database connection issues:
1. Verify PostgreSQL is running
2. Check your `DATABASE_URL` in the `.env` file
3. Ensure the database exists and the user has appropriate permissions 