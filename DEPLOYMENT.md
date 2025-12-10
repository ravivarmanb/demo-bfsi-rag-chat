# Vercel Deployment Checklist

## ✅ Pre-Deployment Security

- [x] Removed exposed API key from `.env`
- [x] Added `.env` to `.gitignore`
- [ ] **CRITICAL**: Revoke the old API key from Google Cloud Console
- [ ] **CRITICAL**: Generate a new Gemini API key

## ✅ Code Structure

- [x] Restructured FastAPI app for Vercel serverless functions (`api/index.py`)
- [x] Updated `vercel.json` configuration
- [x] Modified Next.js to use relative API paths in production
- [x] Added proper CORS configuration
- [x] Implemented in-memory document storage for serverless
- [x] Used ephemeral ChromaDB for vector storage

## ✅ Configuration Files

- [x] Updated `api/requirements.txt` with minimal dependencies
- [x] Fixed `my-app/next.config.ts` with API rewrites
- [x] Created proper `.gitignore`
- [x] Updated build scripts in `package.json`

## 🚀 Deployment Steps

### 1. Security First
```bash
# Go to https://aistudio.google.com/app/apikey
# 1. Revoke the exposed key: AIzaSyDOBjsNlvJDTJu9UWVY7QLDsxuRA9y9Cek
# 2. Create a new API key
# 3. Copy the new key for Vercel environment variables
```

### 2. Push to GitHub
```bash
git add .
git commit -m "Restructure for Vercel deployment"
git push origin main
```

### 3. Deploy to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. **Set Environment Variables:**
   ```
   GEMINI_API_KEY=your_new_api_key_here
   ```
4. Deploy!

### 4. Test Deployment
- [ ] Visit your Vercel URL
- [ ] Test `/api/health` endpoint
- [ ] Upload a test document
- [ ] Send a chat message
- [ ] Verify responses work

## ⚠️ Known Limitations

### Serverless Constraints
- Documents stored in memory (lost on cold starts)
- Vector database is ephemeral (recreated each time)
- 30-second function timeout limit
- Memory limitations for large documents

### Production Recommendations
For a production app, consider:
- **Persistent Storage**: Pinecone, Weaviate Cloud, or Supabase Vector
- **File Storage**: AWS S3, Google Cloud Storage, or Vercel Blob
- **Caching**: Redis for vector store caching
- **Database**: PostgreSQL with pgvector extension

## 🔧 Local Development

### Run Locally
```bash
# Terminal 1: API
npm run dev:api

# Terminal 2: Frontend  
cd my-app && npm run dev
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# Upload document
curl -X POST -F "file=@test.txt" -F "filename=test.txt" http://localhost:8000/api/upload_document

# Chat
curl -X POST -H "Content-Type: application/json" -d '{"message":"Hello"}' http://localhost:8000/api/chat
```

## 🐛 Troubleshooting

### Common Issues
1. **Cold starts**: First request may be slow (30+ seconds)
2. **Memory errors**: Large documents may fail
3. **Timeout errors**: Complex queries may timeout
4. **CORS errors**: Check API configuration

### Debug Steps
1. Check Vercel function logs
2. Test API endpoints individually  
3. Verify environment variables
4. Check API key permissions

## 📊 Monitoring

After deployment, monitor:
- Function execution time
- Memory usage
- Error rates
- Cold start frequency

Consider upgrading to Vercel Pro for better performance and monitoring.