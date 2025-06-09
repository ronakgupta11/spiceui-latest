# SpiceUI

SpiceUI is a FastAPI application that converts UI designs (images or Figma links) into React code using a specific UI library. The application ingests UI components one at a time and uses them to generate clean, modular React code.

## Features

- **Component Ingestion**: Ingest UI components from JSON metadata or documentation pages
- **Image Annotation**: Annotate images and Figma designs to detect UI components
- **Code Generation**: Generate React code using the matched components
- **Vector Storage**: Store component information in a vector database for semantic search
- **Vision AI**: Use CLIP and DETR models for image understanding and component matching

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spiceui.git
cd spiceui
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
python -m playwright install chromium
```

## Usage

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Ingest Component
```http
POST /api/v1/ingest-component
```
Ingest a component either from metadata or by scraping a documentation URL.

#### 2. Annotate Image
```http
POST /api/v1/annotate
```
Annotate an image or Figma design with detected components.

#### 3. Generate Code
```http
POST /api/v1/generate
```
Generate React code from annotated components.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
/app
├── main.py              # FastAPI application entry point
├── routers/            # API route handlers
│   ├── ingest.py       # Component ingestion endpoints
│   ├── annotate.py     # Image annotation endpoints
│   └── generate.py     # Code generation endpoints
├── agents/             # Core business logic
│   ├── ingestion_agent.py
│   ├── annotation_agent.py
│   └── code_generation_agent.py
├── utils/              # Utility functions
│   ├── scraper.py      # Web scraping utilities
│   ├── vector_store.py # Vector database operations
│   └── vision.py       # Vision AI utilities
└── models/             # Data models
    ├── component_schema.py
    └── request_models.py
```

## Dependencies

- FastAPI: Web framework
- ChromaDB: Vector database
- Playwright: Web scraping
- Transformers: Vision AI models
- Pydantic: Data validation
- Uvicorn: ASGI server

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 


python app/scripts/ingest_components.py