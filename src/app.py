"""
Excuse Email Draft Tool - FastAPI Backend
Generates humorous excuse emails using Databricks Model Serving LLM
"""

import os
import json
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Excuse Email Draft Tool",
    description="Generate creative excuse emails using Databricks Model Serving",
    version="1.0.0"
)

# CORS middleware - allow all origins for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    start_time = time.time()
    logger.info(f"📥 Incoming request: {request.method} {request.url.path}")
    logger.info(f"   Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"📤 Response: {response.status_code} (took {process_time:.2f}s)")
    
    return response

# Configuration from environment variables
class Config:
    DATABRICKS_API_TOKEN = os.getenv("DATABRICKS_API_TOKEN", "")
    DATABRICKS_ENDPOINT_URL = os.getenv(
        "DATABRICKS_ENDPOINT_URL",
        "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
    )
    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DATABRICKS_API_TOKEN:
            logger.warning("⚠️  DATABRICKS_API_TOKEN not set - LLM calls will fail")
        logger.info(f"✓ Configuration loaded:")
        logger.info(f"  - Endpoint: {cls.DATABRICKS_ENDPOINT_URL}")
        logger.info(f"  - Host: {cls.HOST}:{cls.PORT}")
        logger.info(f"  - Token: {'✓ Set' if cls.DATABRICKS_API_TOKEN else '✗ Missing'}")

Config.validate()

# Pydantic models
class ExcuseRequest(BaseModel):
    """Request model for excuse generation"""
    category: str
    tone: str
    seriousness: int
    recipient_name: str
    sender_name: str
    eta_when: str
    
    @validator('seriousness')
    def validate_seriousness(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Seriousness must be between 1 and 5')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = [
            "Running Late", "Missed Meeting", "Deadline", 
            "WFH/OOO", "Social", "Travel"
        ]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v
    
    @validator('tone')
    def validate_tone(cls, v):
        valid_tones = ["Sincere", "Playful", "Corporate"]
        if v not in valid_tones:
            raise ValueError(f'Tone must be one of: {", ".join(valid_tones)}')
        return v

class ExcuseResponse(BaseModel):
    """Response model for excuse generation"""
    subject: str
    body: str
    success: bool = True
    error: Optional[str] = None

# LLM prompt engineering
def build_prompt(request: ExcuseRequest) -> str:
    """Build the LLM prompt based on request parameters"""
    
    seriousness_map = {
        1: "extremely silly and humorous",
        2: "lighthearted with some humor",
        3: "balanced between humorous and professional",
        4: "mostly professional with slight humor",
        5: "completely serious and professional"
    }
    
    tone_instructions = {
        "Sincere": "Use a genuine, heartfelt tone that shows real remorse and responsibility.",
        "Playful": "Use a fun, slightly cheeky tone that's still respectful and appropriate.",
        "Corporate": "Use formal, professional business language with proper corporate etiquette."
    }
    
    category_context = {
        "Running Late": f"running late and will arrive {request.eta_when}",
        "Missed Meeting": f"missed a meeting that was scheduled {request.eta_when}",
        "Deadline": f"missed a deadline that was due {request.eta_when}",
        "WFH/OOO": f"requesting to work from home or be out of office {request.eta_when}",
        "Social": f"unable to attend a social event {request.eta_when}",
        "Travel": f"experiencing travel delays and will arrive {request.eta_when}"
    }
    
    prompt = f"""Write an excuse email about {request.category.lower()} - {category_context[request.category]}.

Tone: {request.tone}
Style: {seriousness_map[request.seriousness]}
From: {request.sender_name}
To: {request.recipient_name}

Create a {request.tone.lower()} email with:
- A brief subject line
- Greeting to {request.recipient_name}
- Creative excuse for {category_context[request.category]}
- Brief explanation
- Sign-off from {request.sender_name}

Respond ONLY with valid JSON (no other text):
{{"subject": "your subject here", "body": "your email here"}}"""
    
    return prompt

async def call_llm(prompt: str) -> Dict[str, Any]:
    """Call Databricks Model Serving endpoint with the prompt"""
    
    if not Config.DATABRICKS_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="DATABRICKS_API_TOKEN not configured. Please set the environment variable."
        )
    
    headers = {
        "Authorization": f"Bearer {Config.DATABRICKS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Try different request formats for compatibility
    request_body = {
        "messages": [
            {
                "role": "system",
                "content": "You are a creative assistant that generates excuse emails. Always respond with valid JSON containing 'subject' and 'body' fields."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.8
    }
    
    logger.info(f"🤖 Calling LLM endpoint: {Config.DATABRICKS_ENDPOINT_URL}")
    logger.info(f"📝 Prompt length: {len(prompt)} characters")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                Config.DATABRICKS_ENDPOINT_URL,
                headers=headers,
                json=request_body
            )
            
            logger.info(f"📊 LLM Response Status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ LLM Error: {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM API error: {error_text}"
                )
            
            response_json = response.json()
            logger.info(f"✓ LLM Response received: {len(str(response_json))} bytes")
            
            return response_json
            
    except httpx.TimeoutException:
        logger.error("⏱️  LLM request timed out")
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except httpx.RequestError as e:
        logger.error(f"🔌 Network error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def parse_llm_response(response_data: Dict[str, Any]) -> Dict[str, str]:
    """Parse LLM response and extract subject and body"""
    
    logger.info(f"🔍 Parsing LLM response structure...")
    
    # Try to extract content from different response formats
    content = None
    
    # Format 1: OpenAI-style response
    if "choices" in response_data and len(response_data["choices"]) > 0:
        choice = response_data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            content = choice["message"]["content"]
        elif "text" in choice:
            content = choice["text"]
    
    # Format 2: Direct content field
    elif "content" in response_data:
        content = response_data["content"]
    
    # Format 3: Databricks-style response
    elif "predictions" in response_data and len(response_data["predictions"]) > 0:
        content = response_data["predictions"][0]
    
    if not content:
        logger.error(f"❌ Could not find content in response: {response_data}")
        raise ValueError("Could not extract content from LLM response")
    
    # Handle case where content is a list (some LLM APIs return lists)
    if isinstance(content, list):
        if len(content) > 0:
            content = content[0]
        else:
            raise ValueError("Content is an empty list")
    
    # Handle case where content is a dict with 'reasoning' and 'summary' structure
    if isinstance(content, dict):
        # Check for reasoning/summary structure
        if 'summary' in content and isinstance(content['summary'], list):
            for item in content['summary']:
                if isinstance(item, dict) and 'text' in item:
                    content = item['text']
                    logger.info("✓ Extracted text from summary structure")
                    break
        # If still a dict, convert to string
        if isinstance(content, dict):
            content = str(content)
    
    # Ensure content is a string
    if not isinstance(content, str):
        content = str(content)
    
    logger.info(f"📄 Extracted content: {content[:100]}...")
    
    # Try to parse as JSON
    try:
        # Clean up the content - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Try to extract JSON from the content if it's embedded in text
        import re
        
        # Find all positions where { appears followed eventually by "subject" and "body"
        # Use a more permissive pattern that allows for nested content
        json_pattern = r'\{\s*"(?:subject|body)"[^}]*"(?:body|subject)"[^}]*\}'
        matches = list(re.finditer(json_pattern, content, re.DOTALL))
        
        if matches:
            # Use the last match (most likely to be the actual response)
            extracted = matches[-1].group(0)
            logger.info(f"✓ Extracted JSON from response: {extracted[:100]}...")
            content = extracted
        else:
            # Try to find JSON by looking for the last opening brace before "subject"
            subject_pos = content.rfind('"subject"')
            if subject_pos > 0:
                # Find the last { before "subject"
                brace_start = content.rfind('{', 0, subject_pos)
                if brace_start >= 0:
                    # Find the matching closing brace
                    brace_count = 0
                    for i in range(brace_start, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                content = content[brace_start:i+1]
                                logger.info(f"✓ Extracted JSON using brace matching: {content[:100]}...")
                                break
        
        parsed = json.loads(content)
        
        if "subject" in parsed and "body" in parsed:
            logger.info("✓ Successfully parsed JSON response")
            return {"subject": parsed["subject"], "body": parsed["body"]}
        else:
            raise ValueError("JSON missing required fields")
            
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  Failed to parse as JSON: {e}")
        
        # Fallback: try to extract subject and body from text
        lines = content.split('\n')
        subject = ""
        body = ""
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'subject:' in line_lower:
                subject = line.split(':', 1)[1].strip()
            elif subject and not body:
                # Everything after subject is body
                body = '\n'.join(lines[i:]).strip()
                break
        
        if not subject:
            subject = "Regarding Your Request"
        
        if not body:
            body = content
        
        logger.info("✓ Used fallback text extraction")
        return {"subject": subject, "body": body}

# API Endpoints

@app.post("/api/generate-excuse", response_model=ExcuseResponse)
async def generate_excuse(request: ExcuseRequest):
    """
    Generate an excuse email based on the provided parameters
    """
    logger.info(f"🎯 Generating excuse: {request.category} / {request.tone} / {request.seriousness}")
    
    try:
        # Build prompt
        prompt = build_prompt(request)
        
        # Call LLM
        llm_response = await call_llm(prompt)
        
        # Parse response
        parsed_email = parse_llm_response(llm_response)
        
        logger.info("✅ Successfully generated excuse email")
        
        return ExcuseResponse(
            subject=parsed_email["subject"],
            body=parsed_email["body"],
            success=True,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating excuse: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate excuse: {str(e)}"
        )

@app.get("/health")
@app.get("/healthz")
@app.get("/ready")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "excuse-email-draft-tool",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return PlainTextResponse("pong")

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return PlainTextResponse(
        "# HELP excuse_tool_up Service is up\n"
        "# TYPE excuse_tool_up gauge\n"
        "excuse_tool_up 1\n"
    )

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment configuration"""
    return {
        "endpoint_url": Config.DATABRICKS_ENDPOINT_URL,
        "token_configured": bool(Config.DATABRICKS_API_TOKEN),
        "token_prefix": Config.DATABRICKS_API_TOKEN[:10] + "..." if Config.DATABRICKS_API_TOKEN else "not set",
        "host": Config.HOST,
        "port": Config.PORT,
        "environment": dict(os.environ)
    }

# Static file serving for React frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend"""
    
    # Try multiple paths to find the index.html
    possible_paths = [
        Path(__file__).parent.parent / "public" / "index.html",  # Development
        Path("/app/public/index.html"),  # Databricks Apps
        Path("public/index.html"),  # Alternative
        Path("./public/index.html"),  # Current directory
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"✓ Serving frontend from: {path}")
            return HTMLResponse(content=path.read_text(), status_code=200)
    
    logger.error("❌ Could not find index.html in any expected location")
    logger.error(f"   Tried paths: {[str(p) for p in possible_paths]}")
    
    # Return a basic error page
    return HTMLResponse(
        content="""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Application Error</h1>
                <p>Could not load the frontend. Please check the deployment.</p>
            </body>
        </html>
        """,
        status_code=500
    )

# Application startup
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("🚀 Excuse Email Draft Tool Starting")
    logger.info("=" * 60)
    Config.validate()
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )

