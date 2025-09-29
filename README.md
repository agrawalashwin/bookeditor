# BookEditor - AI Developmental Editor

A lightweight, reliable editing companion for manuscripts that provides AI-powered editing suggestions with clear before/after diffs and version management.

## Features

- **Split-pane editor** with manuscript viewer and edit console
- **AI-powered edit suggestions** with multiple options (light/medium/bold)
- **Vector-based context retrieval** for relevant suggestions
- **Version management** with full manuscript history
- **Export functionality** to Markdown and DOCX formats
- **Style preferences** for consistent editing voice
- **Real-time diff visualization** with before/after comparison

## Architecture

- **Frontend**: Next.js (React) with TypeScript
- **Backend**: FastAPI (Python) with async support
- **Database**: PostgreSQL with pgvector for embeddings
- **AI**: OpenAI GPT-4 for edit suggestions and embeddings
- **Deployment**: Docker Compose for local development

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+ and Poetry
- OpenAI API key

### Setup

1. **Clone and install dependencies:**

   ```bash
   git clone https://github.com/yourusername/bookeditor.git
   cd bookeditor
   make install
   ```

2. **Set up environment:**
   ```bash
   # Copy and edit the API environment file
   cp api/.env.example api/.env.dev
   # Edit api/.env.dev and add your OpenAI API key
   ```

3. **Start services:**
   ```bash
   # Start PostgreSQL
   make docker-up

   # Run database migrations
   make migrate

   # Create demo data
   make seed
   ```

4. **Start development servers:**
   ```bash
   # Terminal 1: API server
   make api

   # Terminal 2: Web frontend
   make web
   ```

5. **Open the application:**
   - Web UI: http://localhost:3000
   - API docs: http://localhost:8000/docs

## Usage

1. **Select text** in the manuscript viewer (left pane)
2. **Enter editing instruction** in the edit console (right pane)
3. **Review AI suggestions** with diff visualization
4. **Apply chosen edit** to update the manuscript
5. **Export** to Markdown or DOCX when ready

### Example Instructions

- "Tighten and improve clarity"
- "Add more suspense and tension"
- "Improve flow and transitions"
- "Make more concise"
- "Enhance descriptive language"

## API Endpoints

### Manuscripts
- `POST /manuscripts/` - Create manuscript
- `GET /manuscripts/{id}` - Get manuscript metadata
- `GET /manuscripts/{id}/content` - Get manuscript content
- `POST /manuscripts/{id}/export?format=markdown|docx` - Export manuscript
- `PUT /manuscripts/{id}/style` - Update style preferences

### Edits
- `POST /edits/suggest` - Generate edit suggestions
- `POST /edits/apply` - Apply chosen edit

## Development

### Project Structure
```
bookeditor/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── models.py      # Database models
│   │   ├── routes/        # API endpoints
│   │   └── services/      # Business logic
│   ├── alembic/           # Database migrations
│   └── seed.py           # Demo data creation
├── web/                   # Next.js frontend
│   └── src/
│       ├── components/    # React components
│       ├── lib/          # API client
│       └── pages/        # Next.js pages
└── docker-compose.yml    # Local development setup
```

### Key Components

**Backend Services:**
- `EmbeddingService` - Text chunking and vector embeddings
- `LLMService` - AI edit suggestion generation
- `DiffService` - Text diff computation and application
- `ExportService` - Document export functionality

**Frontend Components:**
- `BookEditor` - Main application container
- `ManuscriptViewer` - Text display with selection
- `EditConsole` - Edit instruction and options UI
- `DiffViewer` - Before/after diff visualization

### Environment Variables

```bash
# API (.env.local)
DATABASE_URL=postgresql://bookeditor:password@localhost:5432/bookeditor
OPENAI_API_KEY=your_openai_api_key_here
EMBED_MODEL=text-embedding-3-large
GEN_MODEL=gpt-4o-mini

# Web (optional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

```bash
# Run all tests
make test

# API tests only
cd api && poetry run pytest

# Web tests only
cd web && npm test
```

## Deployment

The application is designed for easy deployment with Docker:

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
