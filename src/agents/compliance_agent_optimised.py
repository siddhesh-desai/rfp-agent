import os
import logging
import textwrap
from typing import List, Dict, Any, Optional
from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from agents.prompts import COMPLIANCE_AGENT_PROMPT, COMPLIANCE_RAG_PROMPT
from agents.query_agent import QueryAgent

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# --- Pydantic Models ---
class importanceEnum(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceCriterion(BaseModel):
    criteria: str = Field(
        description="Concise description of the specific eligibility criterion identified and compared (e.g., 'Required Service Scope', 'Minimum Years Experience', etc.)."
    )
    required: str = Field(
        description="The specific requirement detail extracted directly from the RFP text."
    )
    importance: importanceEnum = Field(
        description="The importance of the requirement according to the RFP"
    )

    current: str = Field(
        description="The corresponding status, value, or capability extracted directly from the company profile text. Use `not found` if missing."
    )
    matches: bool = Field(
        description="True if the company's 'current' status meets the 'required' detail based only on the provided texts."
    )
    corrective_steps: Optional[List[str]] = Field(
        description="List of specific corrective steps to take if 'matches' is false."
    )


class ComplianceReport(BaseModel):
    compliance_criteria: List[ComplianceCriterion] = Field(
        description="List of compliance checks comparing RFP requirements against the company profile."
    )
    overall_eligibility_assessment: str = Field(
        description="Brief summary assessing eligibility, including the company's legal name."
    )


# --- Compliance Agent ---
class ComplianceAgent:
    """
    Analyzes RFP text against company profile using Google Gemini
    and returns a structured JSON compliance report.
    """

    def __init__(self, model: str = "gemini-1.5-flash-latest"):
        google_api_key = os.getenv("GEMINI_API_KEY")

        if not google_api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise ValueError("GEMINI_API_KEY environment variable must be set.")

        try:
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0,
                convert_system_message_to_human=True,
            )
            self.structured_llm = llm.with_structured_output(ComplianceReport)
            logger.info(f"Initialized Gemini model '{model}' with structured output.")
        except Exception as e:
            logger.exception("Failed to initialize Gemini model.")
            raise

        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(COMPLIANCE_AGENT_PROMPT)
        )

    def invoke(
        self, rfp_text: str, company_profile: str, filename=None
    ) -> Dict[str, Any]:
        if not rfp_text or not company_profile:
            logger.error("RFP text or Company Profile text is empty.")
            return {"error": "RFP or Company Profile text cannot be empty."}

        try:
            logger.info("Creating and invoking dynamic analysis chain...")

            # Comment Here
            # query_agent = QueryAgent()
            # rfp_text = query_agent.retrieve_relevant_data(
            #     COMPLIANCE_RAG_PROMPT, "test", filename, top_k=1
            # )
            # print(rfp_text)

            chain = self.prompt_template | self.structured_llm
            response = chain.invoke(
                {"rfp_text": rfp_text, "company_profile": company_profile}
            )
            logger.info("Received structured response successfully.")
            return response.dict()
        except Exception as e:
            logger.exception("Error during Gemini model invocation.")
            return {"error": f"Failed to generate compliance report: {str(e)}"}


# --- Main Execution ---
if __name__ == "__main__":
    load_dotenv()

    agent = ComplianceAgent()

    rfp_text = (
        "This RFP requires a minimum of 5 years of experience in IT auditing, "
        "a presence in New York City, and certifications such as CISSP or CISA. "
        "Additionally, the company must provide evidence of $1M liability insurance coverage."
    )

    company_profile = """
    Company Legal Name: Tech Solutions Inc.
    Location: New York City, NY
    Years in Business: 7 years
    Services Offered: IT Auditing, Cybersecurity Consulting, Risk Assessment
    Certifications: CISSP, CISA, ISO 27001 Certified
    Insurance Coverage: $1M General Liability Insurance, $500K E&O Insurance
    Key Personnel: Certified IT Auditors, Cybersecurity Analysts
    """

    response = agent.invoke(rfp_text, company_profile)
    print(response)
