#  Tender Compliance Validator

##  The Problem

In large-scale procurement processes, organizations release detailed Request for Proposal (RFP) documents containing strict technical, legal, and financial requirements. Vendors submit equally complex proposals, and manually verifying compliance against each requirement is time-consuming, error-prone, and inefficient. Missing even a single mandatory requirement can lead to disqualification or legal risks.

---

##  The Solution

The Tender Compliance Validator is an AI-powered system that automates the entire compliance-checking process.

It extracts mandatory requirements from RFP documents, compares vendor proposals against these requirements using semantic analysis, and identifies missing or partially fulfilled conditions. Additionally, it detects hidden risks in vendor documents and provides a compliance score along with a detailed validation report.

###  Key Features

- **Requirement Extraction Engine**
  - Detects mandatory clauses using keywords like *must, shall, required*
  - Categorizes into Technical, Legal, Financial, Operational

- **Bid-to-Requirement Validation**
  - Matches vendor responses using AI (even if wording differs)
  - Flags requirements as *Met*, *Partially Met*, or *Missing*
  - Provides confidence score for each validation

- **Risk Detection System**
  - Identifies risky clauses like *“subject to change”*, *“limited liability”*
  - Classifies risks (High / Medium / Low)
  - Explains impact clearly

- **Compliance Dashboard**
  - Displays vendor comparison
  - Shows compliance score and risk distribution
  - Detailed requirement-wise validation view

-  **Exportable Report**
  - Generates a PDF report for decision-making

---

##  Tech Stack

###  Programming Languages
- Python
- JavaScript
- HTML/CSS

###  Frameworks & Libraries
- FastAPI (Backend API)
- Jinja2 (Templating)
- ReportLab (PDF generation)

###  AI & APIs
- Groq API (LLaMA 3.3 70B model for NLP tasks)

###  File Processing
- pdfplumber (PDF text extraction)

### Deployment
- Railway  (Cloud hosting)

---

##  Setup Instructions

Follow these steps to run the project locally:

###  Clone the Repository
```bash
git clone https://github.com/your-username/tender-validator.git
cd tender-validator
