"""
Security Architecture Framework Agent v4
LangChain + Gemini 2.5 Flash + FastAPI + ChromaDB RAG
"""

import os, json, re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from knowledge_base import get_citations
from rag_retriever import init_rag, retrieve_for_requirement, format_citation

load_dotenv()

app = FastAPI(title="Security Architecture Framework Agent v4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_KEY = os.getenv("GOOGLE_API_KEY")
print(f"API Key loaded: {'YES' if API_KEY else 'NO'}")

RAG_AVAILABLE = init_rag()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY,
    temperature=0.2,
    max_tokens=8000,
)

MAPPING_SYSTEM = (
    "You are a Senior Security Architect Agent with expert knowledge of SABSA, TOGAF, "
    "Zachman, NIST CSF 2.0, Zero Trust (NIST SP 800-207), and NAF/DODAF frameworks.\n\n"
    "Given an organization profile, produce TWO things:\n\n"
    "1. A 3-5 sentence analyst rationale explaining which frameworks apply (macro) and which "
    "specific viewpoints/artifacts matter (micro). Be explicit about exclusions.\n\n"
    "2. A JSON block starting with <<<JSON and ending with >>> with this structure:\n"
    "<<<JSON\n"
    "{\n"
    '  "analysis": "one sentence summary",\n'
    '  "framework_blend": {\n'
    '    "primary": ["framework names"],\n'
    '    "supporting": ["framework names"],\n'
    '    "excluded": ["framework - reason"]\n'
    "  },\n"
    '  "rows": [\n'
    "    {\n"
    '      "requirement": "Security requirement name",\n'
    '      "domain": "Identity|Network|Data|Application|Governance|Cloud Security|Detection & Response|API Security",\n'
    '      "priority": "High|Medium|Low",\n'
    '      "frameworks": {\n'
    '        "SABSA":      {"fit": "primary|secondary|optional|none", "artifact": "artifact name or empty string"},\n'
    '        "TOGAF":      {"fit": "primary|secondary|optional|none", "artifact": "phase or artifact or empty string"},\n'
    '        "Zachman":    {"fit": "primary|secondary|optional|none", "artifact": "row+column or empty string"},\n'
    '        "NIST CSF":   {"fit": "primary|secondary|optional|none", "artifact": "function.category or empty string"},\n'
    '        "Zero Trust": {"fit": "primary|secondary|optional|none", "artifact": "pillar name or empty string"},\n'
    '        "NAF/DODAF":  {"fit": "primary|secondary|optional|none", "artifact": "view name or empty string"}\n'
    "      }\n"
    "    }\n"
    "  ]\n"
    "}\n"
    ">>>\n\n"
    "RULES:\n"
    "- Generate exactly 10 requirements tailored to stated objectives\n"
    "- SABSA: always anchor for business-outcome driven objectives\n"
    "- TOGAF: include for enterprise transformation or migration\n"
    "- Zachman: include for completeness, traceability, governance\n"
    "- NIST CSF: include for compliance or risk management contexts\n"
    "- Zero Trust: include for cloud-first, modernization, API-first, AI-native\n"
    "- NAF/DODAF: ONLY for defense/government contexts, use none for commercial orgs\n"
    "- Use none generously. Be specific with artifact names."
)

DIAGRAM_SYSTEM = (
    "You are a Senior Security Architect Agent. Given an organization profile and objectives, "
    "generate a conceptual security reference architecture as structured JSON.\n\n"
    "Output ONLY a JSON block starting with <<<JSON and ending with >>>:\n"
    "<<<JSON\n"
    "{\n"
    '  "title": "Conceptual Security Reference Architecture",\n'
    '  "objective": "one sentence describing the architecture purpose",\n'
    '  "layers": [\n'
    "    {\n"
    '      "name": "Layer name",\n'
    '      "color": "blue|teal|purple|amber|green|coral",\n'
    '      "components": [\n'
    '        {"name": "Component name", "desc": "5 words max", "framework_ref": "SABSA-L2|TOGAF-PhC|ZT-ID|NIST-PR.AA"}\n'
    "      ]\n"
    "    }\n"
    "  ],\n"
    '  "cross_cutting": [{"name": "concern", "desc": "5 words max"}]\n'
    "}\n"
    ">>>\n\n"
    "Generate 5-6 layers each with 3-4 components specific to the org objectives. "
    "Color: blue=identity, teal=data, purple=governance, amber=operations, green=infrastructure, coral=application."
)

class OrgProfile(BaseModel):
    org_type: str
    regulatory: str = "Not specified"
    maturity: str
    objectives: List[str]
    context: str = ""

class AnalysisResponse(BaseModel):
    analysis_text: str
    mapping: dict
    rag_active: bool

class DiagramResponse(BaseModel):
    diagram: dict

def extract_json(raw: str) -> dict:
    print("\n" + "="*50)
    print(raw[:3000])
    print("="*50 + "\n")
    match = re.search(r'<<<JSON\s*([\s\S]*?)(?:\s*>>>|$)', raw)
    if not match:
        raise ValueError("No JSON block found in response")
    json_str = re.sub(r'```json|```', '', match.group(1)).strip()
    return json.loads(json_str)

def build_user_message(profile: OrgProfile) -> str:
    return (
        f"Organization Type: {profile.org_type}\n"
        f"Regulatory Environment: {profile.regulatory}\n"
        f"Architecture Maturity: {profile.maturity}\n"
        f"Strategic Objectives: {', '.join(profile.objectives)}\n"
        f"Additional Context: {profile.context or 'None provided'}"
    )

async def call_llm(system: str, user: str) -> str:
    resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content

def get_all_citations(rows: list, objectives: list = None) -> None:
    seen_ids = set()
    # Check if AI-native objective is present
    ai_native = objectives and any("AI" in o or "ai" in o.lower() for o in objectives)

    for row in rows:
        domain = row.get("domain", "")
        active_fws = [fw for fw, d in row.get("frameworks", {}).items()
                      if d.get("fit") in ("primary", "secondary")]
        req_name = row.get("requirement", "")
        row_citations = []

        if RAG_AVAILABLE:
            # Always query the 6 core frameworks
            passages = retrieve_for_requirement(req_name, domain, active_fws)
            for p in passages:
                cite = format_citation(p)
                if cite["id"] not in seen_ids:
                    seen_ids.add(cite["id"])
                    row_citations.append(cite)

            # Additionally query AI RMF for AI-native objectives or AI/Governance domains
            if ai_native or "AI" in req_name or domain == "Governance":
                ai_passages = retrieve_for_requirement(
                    req_name, domain, ["NIST AI RMF", "AI Security"]
                )
                for p in ai_passages:
                    cite = format_citation(p)
                    if cite["id"] not in seen_ids:
                        seen_ids.add(cite["id"])
                        row_citations.append(cite)

        rag_fws = {c["framework"] for c in row_citations}
        kb_fws = [fw for fw in active_fws if fw not in rag_fws]
        for c in get_citations(domain, kb_fws):
            c["type"] = "kb"
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                row_citations.append(c)

        row["citations"] = row_citations

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "gemini-2.5-flash",
        "api_key": bool(API_KEY),
        "rag_active": RAG_AVAILABLE,
        "frameworks": ["SABSA","TOGAF","Zachman","NIST CSF","Zero Trust","NAF/DODAF"]
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(profile: OrgProfile):
    if not profile.org_type or not profile.maturity or not profile.objectives:
        raise HTTPException(status_code=400, detail="org_type, maturity, and objectives are required")
    try:
        print(f"\n[ANALYZE] {profile.org_type} | {profile.objectives}")
        raw = await call_llm(MAPPING_SYSTEM, build_user_message(profile))
        mapping = extract_json(raw)
        analysis_text = re.sub(r'<<<JSON[\s\S]*?(?:>>>|$)', '', raw).strip()
        get_all_citations(mapping.get("rows", []), objectives=profile.objectives)
        print(f"[ANALYZE] SUCCESS: {len(mapping.get('rows',[]))} reqs | RAG={'ON' if RAG_AVAILABLE else 'OFF'}")
        return AnalysisResponse(analysis_text=analysis_text, mapping=mapping, rag_active=RAG_AVAILABLE)
    except Exception as e:
        print(f"[ANALYZE] ERROR: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagram", response_model=DiagramResponse)
async def diagram(profile: OrgProfile):
    if not profile.org_type or not profile.objectives:
        raise HTTPException(status_code=400, detail="org_type and objectives are required")
    try:
        print(f"\n[DIAGRAM] {profile.org_type} | {profile.objectives}")
        raw = await call_llm(DIAGRAM_SYSTEM, build_user_message(profile))
        diag = extract_json(raw)
        print(f"[DIAGRAM] SUCCESS: {len(diag.get('layers',[]))} layers")
        return DiagramResponse(diagram=diag)
    except Exception as e:
        print(f"[DIAGRAM] ERROR: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
