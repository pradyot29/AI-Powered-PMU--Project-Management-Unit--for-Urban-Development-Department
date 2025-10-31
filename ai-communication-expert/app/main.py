from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import os

from app.core.config import settings
from app.models.schemas import (
    DocumentRequest, DocumentResponse, 
    HealthCheck, TemplateInfo, DocumentType
)
from app.models.database import init_db, get_db, GeneratedDocument
from app.services.ai_service import AIService
from app.services.document_service import DocumentGenerator

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered communication expert for government PMU"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_service = AIService()
doc_generator = DocumentGenerator()

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} started successfully!")
    print(f"📊 Database: {settings.DATABASE_URL}")
    print(f"🤖 Primary AI: {settings.PRIMARY_LLM} - {settings.MODEL_NAME}")

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Check system health"""
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        ai_service=settings.PRIMARY_LLM,
        database="connected"
    )

# Get available templates
@app.get("/templates", response_model=List[TemplateInfo])
async def get_templates():
    """Get list of available document templates"""
    templates = ai_service.get_available_templates()
    return [
        TemplateInfo(
            id=t["id"],
            name=t["name"],
            document_type=t["document_type"],
            description=t["description"],
            required_fields=["subject", "content"],
            sample=f"Sample {t['name']}"
        )
        for t in templates
    ]

# Generate document endpoint
@app.post("/generate", response_model=DocumentResponse)
async def generate_document(
    request: DocumentRequest,
    db: Session = Depends(get_db)
):
    """Generate government document using AI"""
    try:
        # Generate content using AI
        ai_result = await ai_service.generate_document(request)
        
        # Create document ID
        doc_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate PDF and DOCX
        files = doc_generator.generate_both_formats(
            content=ai_result["content"],
            doc_type=request.document_type.value,
            doc_id=doc_id
        )
        
        # Save to database
        db_document = GeneratedDocument(
            document_type=request.document_type.value,
            subject=request.subject,
            generated_content=ai_result["content"],
            sender_name=request.sender_name,
            sender_designation=request.sender_designation,
            recipient_name=request.recipient_name,
            recipient_organization=request.recipient_organization,
            reference_number=request.reference_number,
            priority=request.priority.value,
            docx_path=files.get("docx_path"),
            pdf_path=files.get("pdf_path"),
            tokens_used=ai_result["tokens_used"],
            cost_estimate=ai_result["cost_estimate"],
            model_used=ai_result["model_used"],
            metadata_json={
                "attachments": request.attachments,
                "additional_context": request.additional_context,
                "meeting_date": request.meeting_date,
                "meeting_venue": request.meeting_venue,
                "attendees": request.attendees,
                "agenda_items": request.agenda_items
            }
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return DocumentResponse(
            id=db_document.id,
            document_type=db_document.document_type,
            generated_content=db_document.generated_content,
            file_path=files.get("docx_path"),
            pdf_path=files.get("pdf_path"),
            docx_path=files.get("docx_path"),
            metadata=db_document.metadata_json or {},
            created_at=db_document.created_at,
            tokens_used=db_document.tokens_used,
            cost_estimate=db_document.cost_estimate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

# Get document by ID
@app.get("/documents/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve a generated document"""
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document.to_dict()

# List all documents
@app.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    document_type: str = None,
    db: Session = Depends(get_db)
):
    """List all generated documents"""
    query = db.query(GeneratedDocument)
    
    if document_type:
        query = query.filter(GeneratedDocument.document_type == document_type)
    
    documents = query.order_by(GeneratedDocument.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": query.count(),
        "documents": [doc.to_dict() for doc in documents]
    }

# Download file
@app.get("/download/{document_id}/{file_type}")
async def download_file(
    document_id: str,
    file_type: str,
    db: Session = Depends(get_db)
):
    """Download generated document file"""
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = document.pdf_path if file_type == "pdf" else document.docx_path
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf" if file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(file_path)
    )

# Statistics endpoint
@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get usage statistics"""
    total_documents = db.query(GeneratedDocument).count()
    total_tokens = db.query(GeneratedDocument).with_entities(
        db.func.sum(GeneratedDocument.tokens_used)
    ).scalar() or 0
    total_cost = db.query(GeneratedDocument).with_entities(
        db.func.sum(GeneratedDocument.cost_estimate)
    ).scalar() or 0.0
    
    # Documents by type
    doc_types = db.query(
        GeneratedDocument.document_type,
        db.func.count(GeneratedDocument.id)
    ).group_by(GeneratedDocument.document_type).all()
    
    return {
        "total_documents": total_documents,
        "total_tokens_used": int(total_tokens),
        "total_cost_estimate": round(float(total_cost), 4),
        "documents_by_type": {doc_type: count for doc_type, count in doc_types},
        "timestamp": datetime.utcnow().isoformat()
    }

# Simple web interface
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve simple web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Communication Expert - PMU</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #2d3748;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #718096;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .info-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .info-card h3 {
                font-size: 0.9em;
                opacity: 0.9;
                margin-bottom: 10px;
            }
            .info-card p {
                font-size: 1.5em;
                font-weight: bold;
            }
            .features {
                background: #f7fafc;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .features h2 {
                color: #2d3748;
                margin-bottom: 15px;
            }
            .features ul {
                list-style: none;
                padding-left: 0;
            }
            .features li {
                padding: 10px;
                margin: 5px 0;
                background: white;
                border-radius: 5px;
                border-left: 4px solid #667eea;
            }
            .features li:before {
                content: "✓ ";
                color: #667eea;
                font-weight: bold;
                margin-right: 10px;
            }
            .btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 8px;
                margin: 10px 10px 10px 0;
                font-weight: bold;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .endpoints {
                background: #2d3748;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-top: 30px;
            }
            .endpoints h2 {
                margin-bottom: 15px;
            }
            .endpoint {
                background: #4a5568;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
            .endpoint .method {
                display: inline-block;
                background: #48bb78;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 0.8em;
                font-weight: bold;
                margin-right: 10px;
            }
            .endpoint .method.post {
                background: #ed8936;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏛️ AI Communication Expert</h1>
            <p class="subtitle">Project Management Unit - Urban Development Department</p>
            
            <div class="info-grid">
                <div class="info-card">
                    <h3>Status</h3>
                    <p>🟢 Online</p>
                </div>
                <div class="info-card">
                    <h3>Version</h3>
                    <p>v1.0.0</p>
                </div>
                <div class="info-card">
                    <h3>AI Model</h3>
                    <p>Claude Sonnet 4</p>
                </div>
            </div>
            
            <div class="features">
                <h2>📋 Supported Document Types</h2>
                <ul>
                    <li>Official Letters (As per MOP)</li>
                    <li>Formal Government Emails</li>
                    <li>Meeting Minutes with Action Points</li>
                    <li>Office Memorandums</li>
                    <li>Circulars and Notices</li>
                </ul>
            </div>
            
            <div style="margin: 30px 0;">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/redoc" class="btn">📖 ReDoc</a>
            </div>
            
            <div class="endpoints">
                <h2>🔌 Quick API Reference</h2>
                <div class="endpoint">
                    <span class="method post">POST</span>
                    <span>/generate - Generate document</span>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span>/templates - List templates</span>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span>/documents - List documents</span>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span>/download/{id}/{type} - Download file</span>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span>/stats - Usage statistics</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)