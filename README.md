# SpiceUI

SpiceUI is a powerful tool that converts UI designs into React code using component libraries. It leverages AI to analyze UI designs and generate production-ready React components.

## Features

- Convert UI designs (images/Figma) to React code
- Support for multiple component libraries
- AI-powered component identification and mapping
- Detailed code generation with proper structure
- Component and icon ingestion system
- Vector store for efficient component search

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher (for React development)
- Git

## Installation

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spiceui.git
cd spiceui
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
python -m playwright install chromium
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Create a `.env` file in the frontend directory:
```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
spiceui/
├── app/                  # Backend application
│   ├── agents/          # AI agents for different tasks
│   ├── graph/           # Workflow graph definitions
│   ├── models/          # Data models and schemas
│   ├── routers/         # API endpoints
│   ├── scripts/         # Utility scripts
│   └── utils/           # Helper utilities
├── frontend/            # React frontend application
│   ├── src/            # Source code
│   ├── public/         # Static files
│   └── package.json    # Frontend dependencies
├── data/
│   └── chroma/         # Vector store data
├── component-docs/     # Component documentation
└── icon-docs/         # Icon documentation
```

## Running the Application

### Backend

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend

1. Start the development server:
```bash
cd frontend
npm run dev
# or
yarn dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

- `POST /api/v1/ingest-component`: Ingest a new component
- `POST /api/v1/generate`: Generate code from UI design
- `GET /api/v1/components/{component_id}`: Get component details

## Running Scripts

### Component Ingestion

To ingest components from documentation:

```bash
python -m app.scripts.ingest_components
```

This will:
1. Clear the existing component collection
2. Process all JSON files in the `component-docs` directory
3. Store components in the vector database

### Icon Ingestion

To ingest icons from documentation:

```bash
python -m app.scripts.ingest_icons
```

This will:
1. Process the icon documentation
2. Store icons in the vector database

## Development

### Backend Development

#### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting

Run the formatters:
```bash
black .
isort .
flake8
```

#### Testing

Run tests using pytest:
```bash
pytest
```

### Frontend Development

#### Code Style

The frontend uses:
- ESLint for code linting
- Prettier for code formatting

Run the formatters:
```bash
cd frontend
npm run lint
npm run format
# or
yarn lint
yarn format
```

#### Testing

Run frontend tests:
```bash
cd frontend
npm run test
# or
yarn test
```

## Environment Variables

### Backend
Create a `.env` file in the root directory with:
```env
OPENAI_API_KEY=your_api_key_here
```

### Frontend
Create a `.env` file in the frontend directory with:
```env
VITE_API_URL=http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.