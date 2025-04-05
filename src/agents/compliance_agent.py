import os
import textwrap
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import logging

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
        description="The corresponding status, value, or capability extracted directly from the company profile text. Use '(INFORMATION NOT FOUND!)' if missing."
    )
    matches: bool = Field(
        description="True if the company's 'current' status clearly meets the 'required' detail based *only* on the provided texts, False otherwise or if information is insufficient/missing."
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

    def __init__(self, model: str = "gemini-1.5-flash-latest"):
        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set.")
            raise ValueError("GOOGLE_API_KEY environment variable must be set.")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0,
                convert_system_message_to_human=True,
            )
            self.structured_llm = self.llm.with_structured_output(ComplianceReport)
            logger.info(
                f"Initialized ChatGoogleGenerativeAI model '{model}' with structured output."
            )
        except Exception as e:
            logger.exception(f"Failed to initialize Google AI model: {e}")
            raise

        # --- PROMPT TEMPLATE WITH REFINED 'matches' LOGIC ---
        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(
                """
            **Role:** You are a meticulous Compliance Analyst AI. Your task is to compare a Request for Proposal (RFP) against a Company Profile to determine eligibility based *only* on the text provided.

            **Objective:** Identify the most **significant** eligibility requirements explicitly stated in the RFP. For each requirement found, locate the corresponding information in the Company Profile and perform a direct comparison. Output a single JSON object adhering strictly to the 'ComplianceReport' schema.

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

            1.  **Identify Key RFP Requirements:** Carefully read the **RFP Text**. Extract the most critical and explicit requirements for eligibility. Focus on potential dealbreakers or core qualifications such as:
                *   Scope of work/Service alignment
                *   Minimum years of experience (overall or specific)
                *   Geographic location requirements (state, county, city)
                *   Mandatory certifications (HUB, MBE, DBE, specific technical certs)
                *   Required licenses
                *   Specific technical skills or platform experience mentioned as mandatory
                *   Insurance types and minimum limits explicitly stated
                *   Mandatory actions (e.g., pre-bid meeting attendance)
                *   Required forms/documents submission
                *   Financial stability indicators if explicitly requested (e.g., annual report)
                *   Explicit requirements for personnel qualifications

            2.  **Find Corresponding Company Data:** For each key requirement identified from the RFP, search the **Company Profile Text** for the *directly corresponding* information, status, or capability.

            3.  **Generate Comparison Criteria:** Create a `ComplianceCriterion` object for *each* significant RFP requirement identified. Do **NOT** use a fixed list; the criteria list should reflect only what you found relevant in *this specific RFP*.
                *   Generate a concise `criteria` label describing the comparison point (e.g., "Service Scope Match", "Experience Requirement", "Location Eligibility").
                *   Populate `required` with the exact detail extracted directly from the RFP.
                *   Populate `current` with the exact detail extracted directly from the Company Profile. If no direct corresponding information is found in the Company Profile, use `"(INFORMATION NOT FOUND!)"`.
                *   **Set `matches` based on the following logic:**
                    *   **First, check for numerical comparisons:** If the `required` value specifies a numerical threshold (like minimum years, dollar amounts, maximum limits) and the `current` value contains a corresponding number (even if wording slightly differs, e.g., 'experience in' vs 'business in' for years), attempt to extract the numbers. If the `current` number clearly meets the `required` threshold (e.g., `current_years >= required_minimum_years`, `current_amount <= required_maximum_amount`), set `matches` to `true`.
                    *   **Otherwise (for non-numerical or complex comparisons):** Set `matches` to `true` only if the `current` value *clearly and unambiguously* meets the `required` value based *solely* on the text wording.
                    *   **Default:** In all other cases (including missing information, unclear requirements, failed numerical checks, or ambiguous non-numerical checks), set `matches` to `false`.

            4.  **Specific Handling for Staffing vs. Service RFPs:**
                *   If the RFP requests a specific service (e.g., 'IT Audit', 'Web Development') and the Company Profile primarily lists *personnel staffing* in that domain (e.g., 'IT Staffing'):
                    *   For the 'Scope Match' or 'Project Type' criteria, evaluate if the company explicitly lists capabilities or personnel types relevant to performing the *tasks* described in the RFP scope, even if they don't perform the service *as a firm*.
                    *   If the company profile lists relevant personnel roles (e.g., 'Security Auditor' for an 'IT Audit' RFP), consider the scope potentially matched *from a personnel supply perspective*. Apply the `matches` logic from step 3; if the extracted information leads to `true` (potentially based on the personnel role), you *may* add clarifying text in the `current` field like "Provides qualified IT Audit personnel via staffing services".
                    *   However, remain strict on other requirements. Still evaluate if the RFP requires specific *firm experience* (e.g., "experience conducting 5 audits for schools") which the staffing company profile might lack, or specific insurance types (like E&O) not usually carried by staffing firms. Apply the `matches` logic from step 3 rigorously for these; they will likely result in `false` if the company profile doesn't explicitly meet the requirement for the *firm* itself.

            5.  **Compile Report:** Collect all generated `ComplianceCriterion` objects into the `compliance_criteria` list within the `ComplianceReport` JSON structure.

            6.  **Assess Overall Eligibility (Including Company Name):**
                *   First, **locate the company's legal name** within the provided **Company Profile Text**. Look for a label like "Company Legal Name". Extract this name *exactly* as it appears. If the label is missing, state "Company name not found".
                *   Then, based *only* on the comparison criteria you generated (including the specific handling in step 4), write a brief (1-3 sentence) `overall_eligibility_assessment`.
                *   This assessment **MUST** start by stating the extracted company name (or "Company name not found"). For example: "**[Extracted Company Legal Name]** appears generally eligible/ineligible because...".
                *   Highlight the most critical matching or mismatching factors found. Factor in the interpretation from step 4 when assessing overall eligibility.

            **Output Format:** Return *only* the valid JSON object conforming to the `ComplianceReport` schema. Do not include any other text, comments, or markdown formatting outside the JSON structure.

            ```json
            {{
              "compliance_criteria": [
                // Dynamically generated list based on findings
                {{
                  "criteria": "Generated Label 1",
                  "required": "RFP detail 1",
                  "current": "Company detail 1 or (INFORMATION NOT FOUND!) or Clarification Text",
                  "matches": true/false
                }},
                {{
                  "criteria": "Generated Label 2",
                  "required": "RFP detail 2",
                  "current": "Company detail 2 or (INFORMATION NOT FOUND!)",
                  "matches": true/false
                }}
                // ... more criteria as identified ...
              ],
              // Ensure this field includes the extracted company name
              "overall_eligibility_assessment": "[Extracted Company Legal Name or 'Company name not found'] appears generally eligible/ineligible because..."
            }}
            ```
            """
            )
        )

    def invoke(self, rfp_text: str, company_profile: str) -> Dict[str, Any]:
        # ... (invoke method remains the same) ...
        if not rfp_text or not company_profile:
            logger.error("RFP text or Company Profile text is empty.")
            return {"error": "RFP or Company Profile text cannot be empty."}

        logger.info("Creating dynamic analysis chain with Google model...")
        try:
            chain = self.prompt_template | self.structured_llm
            logger.info("Invoking dynamic analysis chain...")
            response = chain.invoke(
                {"rfp_text": rfp_text, "company_profile": company_profile}
            )
            logger.info("Successfully received structured response from Google model.")
            return response.dict()

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
