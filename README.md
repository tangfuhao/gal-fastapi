# Gala API

A FastAPI project with modern structure and best practices.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn main:app --reload
```

3. Visit the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
gala/
├── main.py          # FastAPI application entry point
├── requirements.txt # Project dependencies
└── README.md       # Project documentation
```


pipreqs . --force 