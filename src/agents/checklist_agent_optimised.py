import os
import logging
import textwrap
from typing import List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from agents.prompts import CHECKLIST_PROMPT, CHECKLIST_RAG_PROMPT
from agents.query_agent import QueryAgent

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---
class ChecklistItem(BaseModel):
    task: str = Field(
        description="The specific task or deliverable extracted from the RFP."
    )
    priority: str = Field(
        description="The priority level of the task (Low, Medium, High)."
    )
    deadline: str = Field(description="The deadline for the task in YYYY-MM-DD format.")


class ChecklistReport(BaseModel):
    items: List[ChecklistItem] = Field(
        description="A list of checklist items extracted from the RFP."
    )


# --- Checklist Agent ---
class ChecklistAgent:
    """
    Uses Google Gemini to analyze RFP text and produce a structured checklist.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise ValueError("GEMINI_API_KEY environment variable must be set.")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0,
                convert_system_message_to_human=True,
            )
            self.structured_llm = self.llm.with_structured_output(ChecklistReport)
            logger.info(f"Initialized Gemini model '{model}' with structured output.")
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini model: {e}")
            raise

        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(CHECKLIST_PROMPT)
        )

    def invoke(self, rfp_text: str, filename=None) -> Dict[str, Any]:
        if not rfp_text.strip():
            logger.error("RFP text cannot be empty.")
            return {"error": "RFP text cannot be empty."}

        logger.info("Running checklist analysis on RFP text...")
        try:
            # Comment Here
            query_agent = QueryAgent()
            rfp_text = query_agent.retrieve_relevant_data(
                CHECKLIST_RAG_PROMPT, "test", filename, top_k=2
            )
            print(rfp_text)

            chain = self.prompt_template | self.structured_llm
            response = chain.invoke({"rfp_text": rfp_text})
            logger.info("Received structured response from Gemini model.")
            return response.dict()
        except Exception as e:
            logger.exception(f"Checklist generation failed: {e}")
            return {"error": f"Checklist generation failed. Error: {str(e)}"}


# --- Example Usage ---
if __name__ == "__main__":
    load_dotenv()
    agent = ChecklistAgent()
    rfp_text = (
        "The project requires the following deliverables: "
        "1. Submit a project plan by 2023-12-01. "
        "2. Complete the initial design by 2024-01-15."
    )
    result = agent.invoke(rfp_text)
    print(result)
