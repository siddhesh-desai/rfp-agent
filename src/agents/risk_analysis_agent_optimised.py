import os
import logging
import textwrap
from typing import List, Dict, Any, Literal

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from agents.prompts import RISK_ANALYSIS_PROMPT, RISK_ANALYSIS_RAG_PROMPT
from agents.query_agent import QueryAgent

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---
class RiskItem(BaseModel):
    risk_description: str = Field(
        description="A clear, concise description of the potential risk or challenge identified for the company when comparing the RFP requirements to the company profile."
    )
    severity: Literal["High", "Medium", "Low"] = Field(
        description="Estimated severity of the risk (High: Potential disqualifier/major obstacle, Medium: Requires significant attention/mitigation, Low: Minor challenge/manageable)."
    )
    mitigation_strategy: str = Field(
        description="A plausible suggestion for how the company might address or mitigate this specific risk."
    )


class RiskAnalysisReport(BaseModel):
    identified_risks: List[RiskItem] = Field(
        description="A list of potential risks identified for the company in relation to this specific RFP, based *only* on the provided texts."
    )


class RiskAnalysisAgent:
    """Analyzes RFP and Company Profile texts to identify potential risks for the bidding company using Google Gemini."""

    def __init__(self, model: str = "gemini-1.5-flash-latest"):
        self.llm = self._initialize_llm(model)
        self.structured_llm = self.llm.with_structured_output(RiskAnalysisReport)
        self.prompt_template = self._build_prompt()

    def _initialize_llm(self, model: str) -> ChatGoogleGenerativeAI:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise ValueError("GEMINI_API_KEY environment variable must be set.")

        try:
            logger.info(f"Initializing Gemini model '{model}'...")
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.1,
                convert_system_message_to_human=True,
            )
        except Exception as e:
            logger.exception(f"Failed to initialize Google AI model: {e}")
            raise

    def _build_prompt(self) -> ChatPromptTemplate:
        template = textwrap.dedent(RISK_ANALYSIS_PROMPT)

        return ChatPromptTemplate.from_template(template)

    def invoke(
        self, rfp_text: str, company_profile: str, filename=None
    ) -> Dict[str, Any]:
        if not rfp_text or not company_profile:
            logger.error("RFP or Company Profile text cannot be empty.")
            return {"error": "RFP or Company Profile text cannot be empty."}

        try:
            logger.info("Running risk analysis...")

            # Comment Here
            query_agent = QueryAgent()
            rfp_text = query_agent.retrieve_relevant_data(
                RISK_ANALYSIS_RAG_PROMPT, "test", filename, top_k=10
            )
            print(rfp_text)

            chain = self.prompt_template | self.structured_llm
            result = chain.invoke(
                {"rfp_text": rfp_text, "company_profile": company_profile}
            )
            logger.info("Risk analysis completed successfully.")
            return result.dict()
        except Exception as e:
            logger.exception(f"Risk analysis failed: {e}")
            return {
                "error": f"Failed to generate risk analysis report. Error: {str(e)}"
            }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    agent = RiskAnalysisAgent()

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

    result = agent.invoke(rfp_text, company_profile)
    print(result)
