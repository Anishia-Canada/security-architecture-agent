"""
Security Architecture Framework Agent
Backend: LangChain + Gemini + FastAPI
"""

import os
import json
import re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

app = FastAPI(title="Security Architecture Framework Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LLM Setup ────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2,
)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Senior Security Architect Agent with expert-level knowledge of the following frameworks:

- SABSA (Sherwood Applied Business Security Architecture): Business-attribute driven, risk and traceability focused. Layers: Contextual, Conceptual, Logical, Physical, Component, Operational. Best for outcome-driven, enterprise-wide security architecture.
- TOGAF (The Open Group Architecture Framework): ADM phases A-H. Security architecture sits within Phase E (Opportunities & Solutions) and Phase F (Migration Planning). Best for large enterprise transformation programs.
- Zachman Framework: 6x6 grid (Why/How/What/Who/Where/When vs Planner/Owner/Designer/Builder/Implementer/Worker). Best for traceability, completeness auditing, and governance.
- NIST CSF 2.0: Functions: Govern, Identify, Protect, Detect, Respond, Recover. Best for risk management baseline and regulatory alignment.
- Zero Trust Architecture (NIST SP 800-207): Pillars: Identity, Devices, Networks, Applications & Workloads, Data, Visibility & Analytics, Automation & Orchestration. Best for cloud-native, modernization, and perimeter-less environments.
- NAF/DODAF/DNDAF: NATO Architecture Framework and DoD Architecture Framework. Viewpoints: Capability, Operational, Service, Technical, Systems. Primarily for defense, government, and allied/coalition environments.

MACRO FRAMEWORK SELECTION RULES:
- SABSA: Always anchor for any business-driven or outcome-driven objective. Provides the WHY.
- TOGAF: Include when organization is undergoing enterprise-wide transformation, migration, or modernization.
- Zachman: Include when completeness, traceability, and governance are priorities. Strong for regulated industries.
- NIST CSF: Include for any organization with compliance or risk management obligations.
- Zero Trust: Include for cloud-first, cloud migration, modernization, API-first, or AI-native objectives.
- NAF/DODAF/DNDAF: Only include for defense, government, or allied/coalition contexts. Mark as "none" for commercial organizations.

MICRO VIEWPOINT SELECTION (specific artifacts per framework):
- SABSA for cloud: Business Attribute Profile, Risk & Threat Model, Logical Security Architecture (Conceptual layer)
- SABSA for modernization: Operational Architecture, Service Management Framework
- TOGAF for cloud migration: Phase B (Business Architecture), Phase E (migration roadmap), Architecture Requirements Specification
- TOGAF for modernization: Phase C (IS Architecture), Phase F (Migration Plan), Gap Analysis
- Zachman for cloud: Row 2 (Owner/Business), Row 3 (Designer/Architect) — What column (Data), How column (Function)
- NIST CSF for cloud: PR.AA (Identity Management), PR.DS (Data Security), DE.CM (Monitoring), GV.RM (Risk Management)
- Zero Trust for cloud: Identity Pillar, Application Workload Pillar, Data Pillar, Visibility & Analytics Pillar
- Zero Trust for modernization: Network Pillar, Device Pillar, Automation & Orchestration Pillar

OUTPUT INSTRUCTIONS:
Respond with exactly two parts in this order:

PART 1 - ANALYSIS (3-5 sentences of analyst-level rationale):
Explain your macro framework selection (which apply and why) and micro selection (which specific viewpoints/artifacts within each framework are most relevant to the stated objectives). Be specific about why certain frameworks are excluded.

PART 2 - JSON MAPPING (start with <<<JSON and end with >>>):
<<<JSON
{{
  "analysis": "one sentence summary of the framework blend rationale",
  "framework_blend": {{
    "primary": ["list of primary frameworks"],
    "supporting": ["list of supporting frameworks"],
    "excluded": ["list of excluded frameworks with one-word reason"]
  }},
  "rows": [
    {{
      "requirement": "Specific security requirement name (concise, noun-phrase)",
      "domain": "One of: Identity, Network, Data, Application, Governance, Cloud Security, Detection & Response, API Security",
      "priority": "High | Medium | Low",
      "frameworks": {{
        "SABSA": {{"fit": "primary|secondary|optional|none", "artifact": "specific artifact name or empty string"}},
        "TOGAF": {{"fit": "primary|secondary|optional|none", "artifact": "specific phase or artifact name or empty string"}},
        "Zachman": {{"fit": "primary|secondary|optional|none", "artifact": "specific row+column or empty string"}},
        "NIST CSF": {{"fit": "primary|secondary|optional|none", "artifact": "specific function.category code or empty string"}},
        "Zero Trust": {{"fit": "primary|secondary|optional|none", "artifact": "specific pillar name or empty string"}},
        "NAF/DODAF": {{"fit": "primary|secondary|optional|none", "artifact": "specific view or empty string"}}
      }}
    }}
  ]
}}
>>>

Generate 10-12 security requirements. Be precise — use "none" generously for frameworks that don't apply. Not every requirement needs all frameworks. Vary the priority levels realistically.
"""

# ── Prompt Template ───────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Analyze this organization and generate the security architecture framework mapping:

Organization Type: {org_type}
Regulatory Environment: {regulatory}
Architecture Maturity: {maturity}
Strategic Objectives: {objectives}
Additional Context: {context}

Generate the framework mapping now.""")
])

chain = prompt | llm | StrOutputParser()

# ── Request / Response Models ─────────────────────────────────────────────────
class OrgProfile(BaseModel):
    org_type: str
    regulatory: str = "Not specified"
    maturity: str
    objectives: List[str]
    context: str = ""

class AnalysisResponse(BaseModel):
    analysis_text: str
    mapping: dict

# ── Parse LLM output ──────────────────────────────────────────────────────────
def parse_response(raw: str) -> tuple[str, dict]:
    json_match = re.search(r'<<<JSON\s*([\s\S]*?)\s*>>>', raw)
    analysis_text = re.sub(r'<<<JSON[\s\S]*?>>>', '', raw).strip()
    
    if not json_match:
        raise ValueError("No JSON block found in model response")
    
    json_str = json_match.group(1).strip()
    mapping = json.loads(json_str)
    return analysis_text, mapping

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Security Architecture Agent running", "model": "gemini-2.0-flash-001"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(profile: OrgProfile):
    if not profile.org_type or not profile.maturity or not profile.objectives:
        raise HTTPException(status_code=400, detail="org_type, maturity, and objectives are required")
    
    try:
        raw = await chain.ainvoke({
            "org_type": profile.org_type,
            "regulatory": profile.regulatory,
            "maturity": profile.maturity,
            "objectives": ", ".join(profile.objectives),
            "context": profile.context or "None provided"
        })
        
        analysis_text, mapping = parse_response(raw)
        return AnalysisResponse(analysis_text=analysis_text, mapping=mapping)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse model JSON output: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "model": "gemini-2.0-flash-001", "frameworks": ["SABSA","TOGAF","Zachman","NIST CSF","Zero Trust","NAF/DODAF"]}

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
