# src/risk_analysis_agent.py

import os
import textwrap
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# --- Pydantic Models ---
class RiskItem(BaseModel):
    risk_description: str = Field(
        description="A clear, concise description of the potential risk or challenge identified for the company when comparing the RFP requirements to the company profile."
    )
    severity: Literal["High", "Medium", "Low"] = Field(
        description="Estimated severity of the risk (High: Potential disqualifier/major obstacle, Medium: Requires significant attention/mitigation, Low: Minor challenge/manageable)."
    )
    mitigation_strategy: str = Field(
        description="A plausible suggestion for how the company might address or mitigate this specific risk (e.g., 'Obtain required E&O insurance', 'Highlight specific personnel experience', 'Request clarification from issuer', 'Allocate additional resources')."
    )


class RiskAnalysisReport(BaseModel):
    identified_risks: List[RiskItem] = Field(
        description="A list of potential risks identified for the company in relation to this specific RFP, based *only* on the provided texts."
    )


class RiskAnalysisAgent:
    """
    Analyzes RFP and Company Profile texts to identify potential risks for the bidding company,
    using Google Gemini.
    """

    def __init__(self, model: str = "gemini-1.5-flash-latest"):
        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set.")
            raise ValueError("GOOGLE_API_KEY environment variable must be set.")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0.1,  # Slightly higher temp might help brainstorming mitigation
                convert_system_message_to_human=True,
            )
            # Bind the *RiskAnalysisReport* structure
            self.structured_llm = self.llm.with_structured_output(RiskAnalysisReport)
            logger.info(
                f"Initialized RiskAnalysisAgent with ChatGoogleGenerativeAI model '{model}' and RiskAnalysisReport structure."
            )
        except Exception as e:
            logger.exception(
                f"Failed to initialize Google AI model for RiskAnalysisAgent: {e}"
            )
            raise

        # --- PROMPT TEMPLATE for Risk Analysis ---
        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(
                """
            **Role:** You are a strategic Risk Analyst AI. Your task is to analyze a Request for Proposal (RFP) and a Company Profile to identify potential risks *for the company* if they were to bid on this RFP.

            **Objective:** Based *only* on comparing the provided texts, identify potential risks stemming from requirement gaps, resource constraints, compliance issues, or ambiguities. For each risk, assess its severity and suggest a plausible mitigation strategy. Output a single JSON object adhering strictly to the 'RiskAnalysisReport' schema.

            **Inputs:**

            **Company Profile Text:**
            ```text
            {company_profile}
            ```

            **RFP Text:**
            ```text
            {rfp_text}
            ```

            **Instructions:**

            1.  **Compare RFP Requirements to Company Profile:** Read both texts carefully. Identify areas where the RFP requirements might pose a challenge or risk to the company based on its stated profile. Look for:
                *   **Gaps in Experience/Skills:** RFP requires specific experience (type, years, technology) that isn't clearly listed in the company profile.
                *   **Scope Challenges:** The RFP scope seems significantly broader than the company's stated services or typical project size (infer cautiously if possible).
                *   **Compliance/Document Gaps:** Missing mandatory certifications, licenses, specific forms, or insurance types/limits mentioned in the RFP but not confirmed in the profile.
                *   **Resource Constraints (Implied):** Very tight deadlines, unusually complex requirements mentioned in the RFP.
                *   **Ambiguity:** Unclear or contradictory requirements in the RFP itself that could lead to misunderstandings or disputes.
                *   **Financial/Contractual Risks:** Mentions of specific penalties, non-standard payment terms, or requirements for financial proof not addressed in the profile (e.g., missing Bank Letter of Creditworthiness if required).
            2.  **Generate Risk Items:** For each significant potential risk identified, create a `RiskItem` object.
                *   `risk_description`: Clearly state the risk (e.g., "RFP requires E&O insurance of $1M, not listed in company profile.", "Company lacks stated experience in specific software 'XYZ' required by RFP.", "Mandatory Form 'HSD Form A' required by RFP, not mentioned in profile.", "Potential scope mismatch: RFP requires audit *services*, company provides audit *personnel* via staffing.").
                *   `severity`: Assign "High", "Medium", or "Low".
                    *   High: Potential disqualifier, major gap (e.g., missing mandatory license, core scope mismatch).
                    *   Medium: Significant gap requiring action (e.g., missing non-critical insurance, lack of specific niche experience).
                    *   Low: Manageable challenge (e.g., need to format proposal carefully, ambiguity needing clarification).
                *   `mitigation_strategy`: Suggest a practical action the company could take (e.g., "Obtain required E&O insurance before bid submission.", "Highlight specific project experience of 'James Wu, Security Auditor'.", "Request clarification on required forms from issuer.", "Clearly state in proposal that services are fulfilled via providing qualified personnel.").
            3.  **Compile Report:** Collect all generated `RiskItem` objects into the `identified_risks` list within the `RiskAnalysisReport` JSON structure. If no significant risks are identified based on the text comparison, return an empty list: `"identified_risks": []`.

            **Output Format:** Return *only* the valid JSON object conforming to the `RiskAnalysisReport` schema. Do not include any other text, comments, or markdown formatting outside the JSON structure.

            ```json
            {{
              "identified_risks": [
                {{
                  "risk_description": "Description of potential risk 1",
                  "severity": "High" | "Medium" | "Low",
                  "mitigation_strategy": "Suggested action for risk 1"
                }},
                {{
                  "risk_description": "Description of potential risk 2",
                  "severity": "High" | "Medium" | "Low",
                  "mitigation_strategy": "Suggested action for risk 2"
                }}
                // ... more risks ...
              ]
            }}
            ```
            """
            )
        )

    def invoke(self, rfp_text: str, company_profile: str) -> Dict[str, Any]:
        """
        Analyzes the RFP and company profile texts for potential risks using the Google model.

        Args:
            rfp_text (str): The full extracted text of the RFP.
            company_profile (str): The full extracted text of the company profile.

        Returns:
            Dict[str, Any]: A dictionary containing the structured risk analysis report or an error message.
        """
        if not rfp_text or not company_profile:
            logger.error("RFP text or Company Profile text is empty for risk analysis.")
            return {
                "error": "RFP or Company Profile text cannot be empty for risk analysis."
            }

        logger.info("Creating risk analysis chain with Google model...")
        try:
            chain = self.prompt_template | self.structured_llm
            logger.info("Invoking risk analysis chain...")
            response = chain.invoke(
                {"rfp_text": rfp_text, "company_profile": company_profile}
            )
            logger.info(
                "Successfully received structured risk analysis response from Google model."
            )
            return response.dict()  # Convert Pydantic model to dictionary

        except Exception as e:
            logger.exception(
                f"Error invoking risk analysis agent with Google model: {e}"
            )
            return {
                "error": f"Failed to generate risk analysis report using Google model. Error: {str(e)}"
            }


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv

    load_dotenv()
    agent = RiskAnalysisAgent()
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
    result = agent.invoke(rfp_text, company_profile)
    print(result)
