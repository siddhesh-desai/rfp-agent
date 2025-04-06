# 🚀 RFPInsight – Automating Government RFP Analysis with GenAI

**RFPInsight** is a Generative AI-powered solution designed to automate the review of complex government RFPs. Built for the ConsultAdd Hackathon, it simplifies legal, compliance, and risk assessments using **RAG (Retrieval-Augmented Generation)** and **agentic workflows**.

---

## 🧩 Problem Statement

ConsultAdd responds to complex government RFPs that require extensive legal, compliance, and risk analysis. Currently, this process is **manual**, **time-consuming**, and **prone to human error**—leading to potential non-compliance, disqualification, and missed opportunities.

As the **volume and complexity of RFPs** grow, there is a **critical need for an AI-powered solution** that:

- ✅ Automates eligibility checks  
- 📋 Extracts key submission requirements  
- ⚠️ Flags contractual risks  
- 🧾 Generates structured submission checklists  

This not only **streamlines the process** but also **improves accuracy** and **saves valuable time**.

---

## 🧠 Solution Architecture

![image](https://github.com/user-attachments/assets/39adfa83-9076-41f4-be30-28e4aaf482b7)


### Key Components:

- **Data Ingestor**  
  - Docling Preprocessor + Context-Aware Chunking  
  - Embeddings using `llama2-text-embedding-2` and Pinecone Vector DB  

- **RAG Agent**  
  - Retrieves relevant RFP context dynamically  

- **Text Extraction & Summarization**  
  - Extracts essential details from unstructured PDFs  

- **Agentic Workflow Pipeline**  
  - **Checklist Agent**: Generates prioritized task lists  
  - **Compliance Agent**: Validates requirements and suggests fixes  
  - **Risk Analyzer Agent**: Flags and ranks contract risks  
  - **Report Generator**: Creates downloadable compliance reports  
  - **Reference Agent**: Finds external supporting documents (news/articles)

- **Chat-with-RFP Q&A Bot** (Optional)  
  - Interactive chatbot for clarifying queries

---

## ✅ Features

| Module              | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| 📂 Eligibility Checker | Matches RFP requirements with ConsultAdd's company data           |
| 📋 Checklist Agent     | Extracts submission requirements, formats, and deadlines         |
| ⚖️ Risk Analyzer        | Flags risky clauses and suggests mitigation strategies          |
| 🧾 Report Generator     | Produces downloadable PDF reports for internal reviews          |
| 🔗 Reference Agent      | Links to external news/articles relevant to the RFP context     |

---

## 🏗️ Tech Stack

- **LangChain + Google Gemini**
- **Llama2 Embeddings + Pinecone Vector DB**
- **Pydantic** (for structured outputs)
- **PyMuPDF / PDFMiner** (for PDF parsing)
- **Streamlit / FastAPI** (optional UI/backend)

---

## 💻 How to Run

1. **Clone the Repo:**
```bash
git clone https://github.com/your-username/rfpinsight.git
cd rfpinsight
