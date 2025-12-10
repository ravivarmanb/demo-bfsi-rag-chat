# RAG Chat App - Vercel Deployment

A full-stack RAG (Retrieval-Augmented Generation) chat application with FastAPI backend and Next.js frontend, optimized for Vercel deployment.

## Features

- 🤖 AI-powered chat using Google Gemini
- 📄 Document upload and knowledge base integration
- 🔍 Vector similarity search with ChromaDB
- 🚀 Serverless deployment on Vercel
- 💾 In-memory document storage (resets on cold starts)

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with serverless functions
- **AI**: Google Gemini 2.0 Flash
- **Vector DB**: ChromaDB (ephemeral for serverless)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.9+
- Google Gemini API key

### Setup

1. **Clone and install dependencies:**
   ```bash
   npm install
   cd my-app && npm install && cd ..
   pip install -r api/requirements.txt
   ```

2. **Environment setup:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Run development servers:**
   
   Terminal 1 (API):
   ```bash
   npm run dev:api
   ```
   
   Terminal 2 (Frontend):
   ```bash
   npm run dev
   ```

4. **Access the app:**
   - Frontend: http://localhost:3000
   - API docs: http://localhost:8000/docs

## Vercel Deployment

### 1. Prepare for deployment

**IMPORTANT**: First revoke your current API key and create a new one:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Revoke the exposed key
3. Create a new API key

### 2. Deploy to Vercel

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Configure environment variables

3. **Set Environment Variables in Vercel:**
   ```
   GEMINI_API_KEY=your_new_gemini_api_key_here
   ```

4. **Deploy:**
   - Vercel will automatically build and deploy
   - The build process handles both Next.js and Python API

### 3. Verify Deployment

- Check the deployment logs for any errors
- Test the `/api/health` endpoint
- Upload a document and test chat functionality

## Important Notes

### Serverless Limitations

- **Document Storage**: Documents are stored in memory and will be lost on cold starts
- **Vector Database**: Uses ephemeral ChromaDB that resets between function invocations
- **File Persistence**: No persistent file storage in serverless environment

### Production Considerations

For production use, consider:
- **Persistent Storage**: Use cloud databases (Pinecone, Weaviate Cloud)
- **File Storage**: Use cloud storage (AWS S3, Google Cloud Storage)
- **Caching**: Implement Redis for vector store caching
- **Rate Limiting**: Add API rate limiting
- **Authentication**: Implement user authentication

## API Endpoints

- `POST /api/chat` - Send chat messages
- `POST /api/upload_document` - Upload documents (.txt files)
- `GET /api/documents` - List uploaded documents
- `DELETE /api/documents/{filename}` - Delete documents
- `GET /api/health` - Health check

## Troubleshooting

### Common Issues

1. **Cold Start Delays**: First request may be slow due to model initialization
2. **Memory Limits**: Large documents may hit Vercel's memory limits
3. **Timeout Issues**: Complex queries may timeout (30s limit)

### Debug Steps

1. Check Vercel function logs
2. Test API endpoints individually
3. Verify environment variables are set
4. Check API key permissions

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| API URL | localhost:8000 | /api |
| Storage | File system | In-memory |
| Vector DB | Persistent | Ephemeral |
| CORS | Localhost only | All origins |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details