from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings
import uuid

Base = declarative_base()

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_type = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    generated_content = Column(Text, nullable=False)
    
    # Metadata
    sender_name = Column(String)
    sender_designation = Column(String)
    recipient_name = Column(String)
    recipient_organization = Column(String)
    reference_number = Column(String)
    priority = Column(String)
    
    # File paths
    docx_path = Column(String)
    pdf_path = Column(String)
    
    # AI metrics
    tokens_used = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    model_used = Column(String)
    
    # Additional data
    metadata_json = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "document_type": self.document_type,
            "subject": self.subject,
            "generated_content": self.generated_content,
            "sender_name": self.sender_name,
            "sender_designation": self.sender_designation,
            "recipient_name": self.recipient_name,
            "recipient_organization": self.recipient_organization,
            "reference_number": self.reference_number,
            "priority": self.priority,
            "docx_path": self.docx_path,
            "pdf_path": self.pdf_path,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "model_used": self.model_used,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()