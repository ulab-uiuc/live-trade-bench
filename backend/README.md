# Live Trade Bench Backend

FastAPI backend for the Live Trade Bench trading dashboard.

## Features

- **Models API**: Trading model performance and management
- **Trades API**: Trading history and statistics
- **News API**: Market news with filtering and search
- **Auto-generated documentation**: Swagger UI and ReDoc
- **CORS support**: Ready for frontend integration

## API Endpoints

### Models
- `GET /api/models` - Get all trading models
- `GET /api/models/{id}` - Get specific model
- `POST /api/models/{id}/toggle` - Toggle model status
- `GET /api/models/{id}/performance` - Get detailed performance metrics

### Trades
- `GET /api/trades` - Get trading history (with pagination and filtering)
- `GET /api/trades/summary` - Get trading performance summary
- `GET /api/trades/stats` - Get detailed trading statistics
- `GET /api/trades/by-symbol/{symbol}` - Get trades by symbol
- `GET /api/trades/by-model/{model}` - Get trades by model

### News
- `GET /api/news` - Get news articles (with filtering and pagination)
- `GET /api/news/{id}` - Get specific news article
- `GET /api/news/category/{category}` - Get news by category
- `GET /api/news/impact/{impact}` - Get news by impact level
- `GET /api/news/search/{query}` - Search news articles
- `GET /api/news/stats/summary` - Get news statistics
- `GET /api/news/trending/topics` - Get trending topics

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python run.py
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

The server runs in development mode with auto-reload enabled. Any changes to the code will automatically restart the server.

## Sample Data

The backend includes sample data for:
- 5 trading models with performance metrics
- 8 recent trades with various symbols
- 8 news articles with different categories and impact levels

## CORS Configuration

CORS is configured to allow requests from:
- http://localhost:3000 (default React dev server)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and configuration
│   ├── schemas.py       # Pydantic models
│   ├── data.py          # Sample data
│   └── routers/         # API route handlers
│       ├── __init__.py
│       ├── models.py    # Trading models endpoints
│       ├── trades.py    # Trading history endpoints
│       └── news.py      # News endpoints
├── requirements.txt     # Python dependencies
├── run.py              # Development server runner
└── README.md           # This file
```