from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    OFFICIAL_LETTER = "official_letter"
    EMAIL = "email"
    MEETING_MINUTES = "meeting_minutes"
    MEMO = "memo"
    CIRCULAR = "circular"
    NOTICE = "notice"

class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class DocumentRequest(BaseModel):
    document_type: DocumentType
    subject: str = Field(..., description="Subject/Title of the document")
    content: str = Field(..., description="Main content or key points")
    recipient_name: Optional[str] = None
    recipient_designation: Optional[str] = None
    recipient_organization: Optional[str] = None
    sender_name: Optional[str] = "Project Director"
    sender_designation: Optional[str] = "Project Director, PMU"
    reference_number: Optional[str] = None
    priority: Priority = Priority.NORMAL
    attachments: Optional[List[str]] = []
    additional_context: Optional[str] = None
    
    # For meeting minutes
    meeting_date: Optional[str] = None
    meeting_venue: Optional[str] = None
    attendees: Optional[List[Dict[str, str]]] = []
    agenda_items: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "official_letter",
                "subject": "Request for Project Status Report",
                "content": "Need status report for Smart City Mission project Phase-2",
                "recipient_name": "Municipal Commissioner",
                "recipient_designation": "Commissioner",
                "recipient_organization": "Municipal Corporation",
                "priority": "high"
            }
        }

class DocumentResponse(BaseModel):
    id: str
    document_type: str
    generated_content: str
    file_path: Optional[str] = None
    pdf_path: Optional[str] = None
    docx_path: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    tokens_used: int
    cost_estimate: float
    
class TemplateInfo(BaseModel):
    id: str
    name: str
    document_type: DocumentType
    description: str
    required_fields: List[str]
    sample: str

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    ai_service: str
    database: str