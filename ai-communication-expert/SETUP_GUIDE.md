# AI Communication Expert - Complete Setup Guide

## 📦 Step-by-Step Installation Guide

### Step 1: System Requirements

**Minimum Requirements:**
- Python 3.9 or higher
- 4GB RAM
- 2GB free disk space
- Internet connection (for AI API calls)

**Recommended:**
- Python 3.11+
- 8GB RAM
- 5GB free disk space
- Stable internet (for optimal AI performance)

### Step 2: Get API Keys

#### Anthropic API Key (Primary - Required)

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy and save it securely

**Pricing**: ~$3 per million input tokens, ~$15 per million output tokens

#### OpenAI API Key (Optional - Fallback)

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API Keys
4. Create new secret key
5. Copy and save it securely

### Step 3: Project Setup

```bash
# 1. Create project directory
mkdir ai-communication-expert
cd ai-communication-expert

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip
```

### Step 4: Create Project Structure

```bash
# Create all required directories
mkdir -p app/api app/core app/models app/services app/utils
mkdir -p templates/government
mkdir -p static outputs tests
```

Your structure should look like:
```
ai-communication-expert/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   ├── schemas.py
│   │   └── database.py
│   ├── services/
│   │   ├── ai_service.py
│   │   └── document_service.py
│   └── utils/
├── templates/
├── static/
├── outputs/
├── tests/
│   └── test_api.py
├── requirements.txt
├── .env
├── .env.example
├── Dockerfile
├── README.md
└── demo.py
```

### Step 5: Create All Files

Copy all the provided code files into their respective locations. I'll provide a checklist:

**Core Files:**
- [ ] `requirements.txt` - Python dependencies
- [ ] `.env.example` - Environment template
- [ ] `app/main.py` - Main FastAPI application
- [ ] `app/core/config.py` - Configuration management

**Model Files:**
- [ ] `app/models/schemas.py` - Pydantic models
- [ ] `app/models/database.py` - SQLAlchemy models

**Service Files:**
- [ ] `app/services/ai_service.py` - AI integration
- [ ] `app/services/document_service.py` - PDF/DOCX generation

**Support Files:**
- [ ] `tests/test_api.py` - Unit tests
- [ ] `demo.py` - Demo script
- [ ] `test_api.sh` - Shell test script
- [ ] `Dockerfile` - Docker configuration
- [ ] `README.md` - Documentation

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Anthropic (Claude API)
- OpenAI (GPT API)
- SQLAlchemy (database)
- python-docx (DOCX generation)
- reportlab (PDF generation)
- And other required packages

### Step 7: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use any text editor
```

**Required Configuration:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx  # Your Anthropic key
OPENAI_API_KEY=sk-xxxxxxxxxxxxx         # Your OpenAI key (optional)

# Customize these as needed
DEPARTMENT_NAME="Urban Development Department"
STATE_NAME="Maharashtra"
OFFICE_ADDRESS="Mantralaya, Mumbai - 400032"
```

### Step 8: Initialize Database

```bash
python -c "from app.models.database import init_db; init_db()"
```

This creates `pmu_communications.db` SQLite database.

### Step 9: Run the Application

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
✅ AI Communication Expert - PMU v1.0.0 started successfully!
📊 Database: sqlite:///./pmu_communications.db
🤖 Primary AI: anthropic - claude-sonnet-4-20250514
INFO:     Application startup complete.
```

### Step 10: Test the Application

**Option 1: Web Browser**
```
Open: http://localhost:8000
```

**Option 2: API Documentation**
```
Open: http://localhost:8000/docs
```

**Option 3: Run Demo Script**
```bash
python demo.py
```

**Option 4: Run Shell Script**
```bash
chmod +x test_api.sh
./test_api.sh
```

**Option 5: Manual cURL Test**
```bash
# Health check
curl http://localhost:8000/health

# Generate document
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "official_letter",
    "subject": "Test Letter",
    "content": "This is a test",
    "priority": "normal"
  }'
```

## 🎯 Quick Start Commands

### Development Mode
```bash
# Start server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
# Start with 4 workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Run Tests
```bash
pytest tests/ -v
```

### Run with Docker
```bash
# Build image
docker build -t ai-comm-expert .

# Run container
docker run -p 8000:8000 --env-file .env ai-comm-expert
```

## 🔧 Troubleshooting

### Issue 1: Import Errors
```bash
# Solution: Ensure you're in the virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: Database Errors
```bash
# Solution: Delete and recreate database
rm pmu_communications.db
python -c "from app.models.database import init_db; init_db()"
```

### Issue 3: API Key Errors
```bash
# Solution: Check your .env file
cat .env | grep API_KEY

# Ensure keys are properly set
export ANTHROPIC_API_KEY="your-key-here"  # Temporary
```

### Issue 4: Port Already in Use
```bash
# Solution: Use different port
uvicorn app.main:app --reload --port 8001

# Or kill the process using port 8000
# On Mac/Linux:
lsof -ti:8000 | xargs kill -9
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 5: Module Not Found
```bash
# Solution: Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
```

## 📊 Verification Checklist

After setup, verify everything works:

- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] API documentation loads at /docs
- [ ] Health check returns "healthy"
- [ ] Can list templates (/templates)
- [ ] Can generate a document (/generate)
- [ ] PDF and DOCX files are created in /outputs
- [ ] Database records are created
- [ ] Statistics endpoint works (/stats)
- [ ] Demo script runs successfully

## 🚀 Next Steps

1. **Customize Templates**: Edit templates in `app/services/ai_service.py`
2. **Add Authentication**: Implement user auth system
3. **Configure Backup**: Set up database backup strategy
4. **Monitor Costs**: Track API usage in statistics
5. **Deploy**: Use Docker or cloud platform for deployment

## 📞 Support

If you face any issues:

1. Check the troubleshooting section above
2. Review the logs in terminal
3. Check API key validity
4. Ensure all dependencies are installed
5. Verify Python version (3.9+)

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Anthropic Docs**: https://docs.anthropic.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **Python DOCX**: https://python-docx.readthedocs.io

---

**Setup Complete! You're ready to generate government documents with AI! 🎉**