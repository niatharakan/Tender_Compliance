from fastapi import FastAPI, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

app = FastAPI()

os.makedirs("uploads", exist_ok=True)

templates = Jinja2Templates(directory="templates")

rfp_text_store = {}
requirements_store = {}
vendors_store = {}

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/checklist")
def checklist_page(request: Request):
    return templates.TemplateResponse(request, "checklist.html", {"request": request})

@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.post("/upload-rfp")
async def upload_rfp(file: UploadFile = File(...)):
    contents = await file.read()
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(contents)
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    rfp_text_store["text"] = text
    return {"message": "RFP uploaded successfully", "length": len(text)}

@app.post("/extract-requirements")
async def extract_requirements():
    if "text" not in rfp_text_store:
        return JSONResponse(status_code=400, content={"error": "No RFP uploaded yet"})

    text = rfp_text_store["text"][:8000]

    prompt = f"""
You are a legal procurement analyst. Read this RFP and extract every mandatory requirement.
Look for sentences with: shall, must, required, mandatory.

Return ONLY a valid JSON array, no explanation, no markdown, no extra text:
[
  {{
    "id": 1,
    "category": "Technical",
    "requirement_text": "The vendor must provide 24/7 support.",
    "keyword_trigger": "must"
  }}
]

Categories must be one of: Technical, Legal, Financial, Operational.

RFP TEXT:
{text}
"""

    raw = ask_ai(prompt).strip().replace("```json", "").replace("```", "").strip()
    requirements = json.loads(raw)
    requirements_store["list"] = requirements
    return {"requirements": requirements}

@app.post("/upload-vendor")
async def upload_vendor(file: UploadFile = File(...)):
    contents = await file.read()
    vendor_name = file.filename.replace(".pdf", "").replace("_", " ").title()
    filepath = f"uploads/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(contents)
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    if "vendors" not in vendors_store:
        vendors_store["vendors"] = {}
    vendors_store["vendors"][vendor_name] = text
    return {"message": f"Vendor {vendor_name} uploaded", "vendor_name": vendor_name}

@app.post("/validate-vendor")
async def validate_vendor(data: dict):
    vendor_name = data.get("vendor_name")
    if vendor_name not in vendors_store.get("vendors", {}):
        return JSONResponse(status_code=400, content={"error": "Vendor not found"})

    proposal_text = vendors_store["vendors"][vendor_name][:8000]
    requirements = requirements_store.get("list", [])
    results = []

    for req in requirements[:15]:
        prompt = f"""
You are a compliance auditor.

REQUIREMENT: "{req['requirement_text']}"

VENDOR PROPOSAL:
{proposal_text}

Does the vendor address this requirement?
Return ONLY this JSON, no explanation, no markdown:
{{
  "status": "Met",
  "confidence": 85,
  "matching_text": "exact quote from proposal or null",
  "reason": "brief explanation"
}}

Status must be one of: Met, Partially Met, Missing
"""
        raw = ask_ai(prompt).strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        result["requirement_id"] = req["id"]
        result["requirement_text"] = req["requirement_text"]
        result["category"] = req["category"]
        results.append(result)

    met = len([r for r in results if r["status"] == "Met"])
    partial = len([r for r in results if r["status"] == "Partially Met"])
    total = len(results)
    compliance_score = round(((met + partial * 0.5) / total) * 100) if total > 0 else 0

    if "results" not in vendors_store:
        vendors_store["results"] = {}

    vendors_store["results"][vendor_name] = {
        "validations": results,
        "compliance_score": compliance_score
    }

    return {"vendor_name": vendor_name, "compliance_score": compliance_score, "validations": results}

@app.post("/detect-risks")
async def detect_risks(data: dict):
    vendor_name = data.get("vendor_name")
    if vendor_name not in vendors_store.get("vendors", {}):
        return JSONResponse(status_code=400, content={"error": "Vendor not found"})

    proposal_text = vendors_store["vendors"][vendor_name][:8000]

    prompt = f"""
You are a contract risk analyst. Find risky clauses in this vendor proposal.
Look for: subject to change, limited liability, additional fees, pending approval,
at our discretion, not responsible, vague commitments.

Return ONLY a valid JSON array, no explanation, no markdown:
[
  {{
    "flagged_text": "exact sentence from document",
    "risk_type": "Liability",
    "severity": "High",
    "impact_summary": "plain English explanation of the risk"
  }}
]

Risk types: Liability, Cost, Vagueness, Commitment, Legal
Severity: High, Medium, Low

PROPOSAL:
{proposal_text}
"""

    raw = ask_ai(prompt).strip().replace("```json", "").replace("```", "").strip()
    risks = json.loads(raw)

    if "risks" not in vendors_store:
        vendors_store["risks"] = {}

    vendors_store["risks"][vendor_name] = risks
    return {"vendor_name": vendor_name, "risks": risks}

@app.get("/dashboard-data")
async def dashboard_data():
    results = vendors_store.get("results", {})
    risks = vendors_store.get("risks", {})
    vendors = []
    for vendor_name, data in results.items():
        vendor_risks = risks.get(vendor_name, [])
        vendors.append({
            "name": vendor_name,
            "compliance_score": data["compliance_score"],
            "total_risks": len(vendor_risks),
            "high_risks": len([r for r in vendor_risks if r.get("severity") == "High"]),
            "medium_risks": len([r for r in vendor_risks if r.get("severity") == "Medium"]),
            "low_risks": len([r for r in vendor_risks if r.get("severity") == "Low"]),
            "validations": data["validations"]
        })
    return {"vendors": vendors}

@app.get("/get-requirements")
async def get_requirements():
    return {"requirements": requirements_store.get("list", [])}