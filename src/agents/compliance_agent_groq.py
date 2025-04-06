import os
import textwrap
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import logging

from agents.prompts import COMPLIANCE_AGENT_PROMPT

# from prompts import COMPLIANCE_AGENT_PROMPT
import os
from groq import Groq
import instructor
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# --- Pydantic Models ---
class ComplianceCriterion(BaseModel):
    # Description remains the same
    criteria: str = Field(
        description="Concise description of the specific eligibility criterion identified and compared (e.g., 'Required Service Scope', 'Minimum Years Experience', 'Location Requirement', 'Specific Certification Needed'). This label should be generated based on the finding."
    )
    required: str = Field(
        description="The specific requirement detail extracted directly from the RFP text."
    )
    current: str = Field(
        description="The corresponding status, value, or capability extracted directly from the company profile text. Use `not found` if missing."
    )
    matches: bool = Field(
        description="True if the company's 'current' status clearly meets the 'required' detail based *only* on the provided texts, False otherwise or if information is insufficient/missing."
    )
    corrective_steps: Optional[List[str]] = Field(
        description="A list of specific corrective steps to take if the 'matches' field is false. This should be a list of actionable items that the company can take to meet the requirement."
    )


class ComplianceReport(BaseModel):
    # Description updated
    compliance_criteria: List[ComplianceCriterion] = Field(
        description="A dynamically generated list of key compliance criteria checks comparing significant RFP requirements against the company profile based *only* on the provided texts."
    )
    overall_eligibility_assessment: str = Field(
        description="A brief summary statement (1-3 sentences) assessing eligibility based solely on identified criteria. MUST explicitly state the company's legal name as found in the input Company Profile Text."
    )


class ComplianceAgent:
    """
    Analyzes RFP text against company profile text (non-RAG) using Google Gemini
    and returns a structured JSON compliance report with dynamically identified criteria.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        # google_api_key = os.getenv("GEMINI_API_KEY")
        # if not google_api_key:
        #     logger.error("GOOGLE_API_KEY environment variable is not set.")
        #     raise ValueError("GOOGLE_API_KEY environment variable must be set.")

        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.client = instructor.from_groq(client)

            # self.llm = ChatGoogleGenerativeAI(
            #     model=model,
            #     google_api_key=google_api_key,
            #     temperature=0,
            #     convert_system_message_to_human=True,
            # )
            # self.structured_llm = self.llm.with_structured_output(ComplianceReport)

            # self.str
            # logger.info(
            #     f"Initialized ChatGoogleGenerativeAI model '{model}' with structured output."
            # )
        except Exception as e:
            logger.exception(f"Failed to initialize Google AI model: {e}")
            raise

        # --- PROMPT TEMPLATE WITH REFINED 'matches' LOGIC ---
        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(COMPLIANCE_AGENT_PROMPT)
        )

    def invoke(self, rfp_text: str, company_profile: str) -> Dict[str, Any]:
        # ... (invoke method remains the same) ...
        if not rfp_text or not company_profile:
            logger.error("RFP text or Company Profile text is empty.")
            return {"error": "RFP or Company Profile text cannot be empty."}

        if len(rfp_text) > 5000:
            logger.error("RFP text is too long.")
            rfp_text = rfp_text[:5000]

        # logger.info("Creating dynamic analysis chain with Google model...")
        # try:
        #     chain = self.prompt_template | self.structured_llm
        #     logger.info("Invoking dynamic analysis chain...")
        #     response = chain.invoke(
        #         {"rfp_text": rfp_text, "company_profile": company_profile}
        #     )
        #     logger.info("Successfully received structured response from Google model.")
        #     return response.dict()

        # except Exception as e:
        #     logger.exception(
        #         f"Error invoking dynamic compliance agent with Google model: {e}"
        #     )
        #     return {
        #         "error": f"Failed to generate compliance report using Google model. Error: {str(e)}"
        #     }
        try:
            response = self.client.chat.completions.create(
                model="qwen-qwq-32b",
                messages=[
                    {
                        "role": "user",
                        "content": self.prompt_template.format(
                            rfp_text=rfp_text, company_profile=company_profile
                        ),
                    },
                ],
                response_model=ComplianceReport,
            )
            print(response)
            return response
        except Exception as e:
            logger.exception(
                f"Error invoking dynamic compliance agent with Google model: {e}"
            )
            return {
                "error": f"Failed to generate compliance report using Google model. Error: {str(e)}"
            }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    # Example usage
    agent = ComplianceAgent()
    rfp_text = "This RFP requires a minimum of 5 years of experience in IT auditing, a presence in New York City, and certifications such as CISSP or CISA. Additionally, the company must provide evidence of $1M liability insurance coverage."
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
