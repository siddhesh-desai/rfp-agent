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


class ChecklistAgent:
    """
    Analyzes RFP text using Google Gemini and returns a structured JSON checklist report.
    """

    def __init__(
        self, model: str = "gemini-2.0-flash"
    ):  # Default to a specific Gemini model
        """
        Initializes the ChecklistAgent with a Google Generative AI model.

        Args:
            model (str): The Google Gemini model name to use (e.g., "gemini-2.5-pro-exp-03-25").
        """
        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set.")
            raise ValueError("GOOGLE_API_KEY environment variable must be set.")

        # Initialize the Google Chat model and bind the structured output format
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0,
                convert_system_message_to_human=True,  # Often needed for Gemini models with system prompts
            )
            self.structured_llm = self.llm.with_structured_output(ChecklistReport)
            logger.info(
                f"Initialized ChatGoogleGenerativeAI model '{model}' with structured output."
            )
        except Exception as e:
            logger.exception(f"Failed to initialize Google AI model: {e}")
            raise

        # Define the prompt template
        self.prompt_template = ChatPromptTemplate.from_template(
            textwrap.dedent(
                """
    You are a helpful assistant designed to extract structured checklists from government RFPs.

    Given the following RFP paragraph, extract:
    1. A checklist of deliverables or steps
    2. For each item, provide:
        - Priority (Low, Medium, High)
        - Deadline (in YYYY-MM-DD format if available)

    Respond ONLY in the following JSON format:

    {{
        "items": [
            {{
                "task": "...",
                "priority": "low | medium | high",
                "deadline": "YYYY-MM-DD"
                    



                    
            }},
            ...
        ]
    }}

    RFP Paragraph:
    {rfp_text}
    """
            )
        )

    def invoke(self, rfp_text: str) -> Dict[str, Any]:
        """
        Analyzes the RFP text using the Google model.

        Args:
            rfp_text (str): The full extracted text of the RFP.

        Returns:
            Dict[str, Any]: A dictionary containing the structured checklist report or an error message.
        """
        if not rfp_text:
            logger.error("RFP text is empty.")
            return {"error": "RFP text cannot be empty."}

        logger.info("Creating analysis chain with Google model...")
        try:
            # Create the chain by combining the prompt and the structured LLM
            chain = self.prompt_template | self.structured_llm
            logger.info("Invoking analysis chain...")
            # Run the chain with the provided RFP text
            response = chain.invoke({"rfp_text": rfp_text})
            # The response should be the Pydantic object ChecklistReport
            logger.info("Successfully received structured response from Google model.")
            return response.dict()  # Convert Pydantic model to dictionary

        except Exception as e:
            logger.exception(f"Error invoking checklist agent with Google model: {e}")
            return {
                "error": f"Failed to generate checklist using Google model. Error: {str(e)}"
            }


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    # Example usage
    agent = ChecklistAgent()
    rfp_text = "The project requires the following deliverables: 1. Submit a project plan by 2023-12-01. 2. Complete the initial design by 2024-01-15."
    result = agent.invoke(rfp_text)
    print(result)
