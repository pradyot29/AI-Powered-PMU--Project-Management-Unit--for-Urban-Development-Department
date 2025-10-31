import anthropic
from openai import OpenAI
from typing import Dict, Any, Optional
from app.core.config import settings
from app.models.schemas import DocumentRequest, DocumentType
import json
from datetime import datetime

class AIService:
    def __init__(self):
        # Initialize clients based on available API keys
        self.anthropic_client = None
        self.openai_client = None
        
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
        # Validate at least one API key exists
        if not self.anthropic_client and not self.openai_client:
            raise ValueError("At least one API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) must be provided")
            
        self.tokens_used = 0
        
    def _get_government_template(self, doc_type: DocumentType) -> str:
        """Returns the government format template for each document type"""
        templates = {
            DocumentType.OFFICIAL_LETTER: """
Format: Official Government Letter (As per Manual of Office Procedure)

[Reference Number]
Date: [Date]

From:
{sender_name}
{sender_designation}
{department_name}
{office_address}

To:
{recipient_name}
{recipient_designation}
{recipient_organization}

Subject: {subject}

Sir/Madam,

[Body of the letter - formal government tone, clear paragraphs]

[Action required/Request]

Thanking you,

Yours faithfully,

[Digital Signature]
{sender_name}
{sender_designation}

Copy to:
1. [Relevant authority]
2. File/Guard File
""",
            DocumentType.MEETING_MINUTES: """
Format: Official Meeting Minutes

MINUTES OF MEETING

Reference No.: [Number]
Date: {meeting_date}
Venue: {meeting_venue}

Subject: {subject}

ATTENDANCE:
[List all attendees with designation]

AGENDA:
[Numbered list of agenda items]

DISCUSSION:
[Point-by-point discussion summary]

DECISIONS TAKEN:
[Numbered list of decisions]

ACTION POINTS:
[Responsibility matrix with timeline]

Meeting concluded at [Time]

Recorded by: [Name]
Approved by: [Chairperson]
""",
            DocumentType.EMAIL: """
Format: Formal Government Email

Subject: {subject}

Dear {recipient_name},

[Professional greeting and context]

[Main content - clear, concise paragraphs]

[Call to action or next steps]

Regards,
{sender_name}
{sender_designation}
{department_name}
Contact: [Phone/Email]
""",
            DocumentType.MEMO: """
Format: Office Memorandum

GOVERNMENT OF {state}
{department_name}

OFFICE MEMORANDUM

No. {reference_number}
Dated: {date}

Subject: {subject}

[Body in numbered paragraphs]

[Signature]
{sender_name}
{sender_designation}

Distribution:
[List of recipients]
""",
            DocumentType.CIRCULAR: """
Format: Government Circular

GOVERNMENT OF {state}
{department_name}

CIRCULAR

No. {reference_number}
Date: {date}

Subject: {subject}

To: [All concerned departments/officials]

[Directive or information in clear points]

This issues with the approval of competent authority.

{sender_name}
{sender_designation}
""",
        }
        return templates.get(doc_type, templates[DocumentType.OFFICIAL_LETTER])
    
    def _build_system_prompt(self, doc_type: DocumentType) -> str:
        """Build system prompt for AI"""
        return f"""You are an expert government communication specialist for the {settings.DEPARTMENT_NAME}, {settings.STATE_NAME}, India.

Your role is to draft official government documents following Indian government protocols, Manual of Office Procedure (MOP), and standard formats.

Key Guidelines:
1. Use formal, professional language appropriate for government communication
2. Follow the exact format structure provided
3. Use respectful salutations (Sir/Madam, Dear, etc.)
4. Include proper reference numbers and dates
5. Maintain hierarchy and protocol
6. Be clear, concise, and action-oriented
7. Use numbered paragraphs for office memorandums
8. Include proper closing formalities
9. Maintain official tone throughout
10. Follow RTI Act compliance where applicable

Current document type: {doc_type.value}

Department: {settings.DEPARTMENT_NAME}
State: {settings.STATE_NAME}
Office: {settings.OFFICE_ADDRESS}"""

    def _build_user_prompt(self, request: DocumentRequest, template: str) -> str:
        """Build user prompt with all details"""
        prompt = f"""Generate a {request.document_type.value} with the following details:

**Subject:** {request.subject}

**Main Content/Purpose:** 
{request.content}

**Document Details:**
- Sender: {request.sender_name} ({request.sender_designation})
- Priority: {request.priority.value}
"""
        
        if request.recipient_name:
            prompt += f"- Recipient: {request.recipient_name}"
            if request.recipient_designation:
                prompt += f" ({request.recipient_designation})"
            if request.recipient_organization:
                prompt += f", {request.recipient_organization}"
            prompt += "\n"
        
        if request.reference_number:
            prompt += f"- Reference Number: {request.reference_number}\n"
        
        if request.additional_context:
            prompt += f"\n**Additional Context:**\n{request.additional_context}\n"
        
        # Special handling for meeting minutes
        if request.document_type == DocumentType.MEETING_MINUTES:
            if request.meeting_date:
                prompt += f"\n**Meeting Date:** {request.meeting_date}"
            if request.meeting_venue:
                prompt += f"\n**Venue:** {request.meeting_venue}"
            if request.attendees:
                prompt += "\n**Attendees:**\n"
                for attendee in request.attendees:
                    prompt += f"- {attendee.get('name', '')} - {attendee.get('designation', '')}\n"
            if request.agenda_items:
                prompt += "\n**Agenda Items:**\n"
                for i, item in enumerate(request.agenda_items, 1):
                    prompt += f"{i}. {item}\n"
        
        if request.attachments:
            prompt += f"\n**Attachments:** {', '.join(request.attachments)}\n"
        
        prompt += f"\n**Format Template to Follow:**\n{template}\n"
        prompt += "\n**Instructions:**\n"
        prompt += "1. Generate a complete, ready-to-use document\n"
        prompt += "2. Fill in today's date where [Date] appears\n"
        prompt += "3. Generate appropriate reference number if not provided\n"
        prompt += "4. Maintain strict government format\n"
        prompt += "5. Do NOT include any explanations or notes - only the document\n"
        prompt += "6. Ensure all placeholders are replaced with actual content\n"
        
        return prompt

    async def generate_document(self, request: DocumentRequest) -> Dict[str, Any]:
        """Generate document using AI"""
        try:
            template = self._get_government_template(request.document_type)
            system_prompt = self._build_system_prompt(request.document_type)
            user_prompt = self._build_user_prompt(request, template)
            
            # Try primary LLM (Anthropic)
            if settings.PRIMARY_LLM == "anthropic":
                response = await self._call_anthropic(system_prompt, user_prompt)
            else:
                response = await self._call_openai(system_prompt, user_prompt)
            
            return {
                "content": response["content"],
                "tokens_used": response["tokens_used"],
                "cost_estimate": self._calculate_cost(response["tokens_used"]),
                "model_used": response["model"]
            }
            
        except Exception as e:
            # Fallback to secondary LLM
            print(f"Primary LLM failed: {str(e)}, trying fallback...")
            try:
                if settings.PRIMARY_LLM == "anthropic" and self.openai_client:
                    response = await self._call_openai(system_prompt, user_prompt)
                else:
                    raise Exception("No fallback available")
                    
                return {
                    "content": response["content"],
                    "tokens_used": response["tokens_used"],
                    "cost_estimate": self._calculate_cost(response["tokens_used"]),
                    "model_used": response["model"] + " (fallback)"
                }
            except Exception as fallback_error:
                raise Exception(f"Both LLMs failed: Primary - {str(e)}, Fallback - {str(fallback_error)}")
    
    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Anthropic Claude API"""
        message = self.anthropic_client.messages.create(
            model=settings.MODEL_NAME,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = message.content[0].text
        tokens = message.usage.input_tokens + message.usage.output_tokens
        
        return {
            "content": content,
            "tokens_used": tokens,
            "model": settings.MODEL_NAME
        }
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        response = self.openai_client.chat.completions.create(
            model=settings.FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE
        )
        
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        return {
            "content": content,
            "tokens_used": tokens,
            "model": settings.FALLBACK_MODEL
        }
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost based on tokens"""
        # Claude Sonnet 4 pricing (approximate)
        input_cost_per_mtok = 3.00  # $3 per million input tokens
        output_cost_per_mtok = 15.00  # $15 per million output tokens
        
        # Assuming 60% input, 40% output split
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1_000_000 * input_cost_per_mtok + 
                output_tokens / 1_000_000 * output_cost_per_mtok)
        
        return round(cost, 6)
    
    def get_available_templates(self) -> list:
        """Return list of available document templates"""
        return [
            {
                "id": dt.value,
                "name": dt.value.replace("_", " ").title(),
                "document_type": dt.value,
                "description": f"Generate {dt.value.replace('_', ' ')} in government format"
            }
            for dt in DocumentType
        ]