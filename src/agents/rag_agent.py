import os
import textwrap
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RAGAgent:

    def __init__(
        self, model: str = "gemini-1.5-flash-latest"
    ):  # Default to a specific Gemini model

        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set.")
            raise ValueError("GOOGLE_API_KEY environment variable must be set.")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0,
                convert_system_message_to_human=True,  # Often needed for Gemini models with system prompts
            )
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
                You are an RFP Agent with deep understanding of government RFPs, RFIs, and procurement documents. Use the provided context retrieved via a RAG mechanism to answer the question as accurately and comprehensively as possible.

                Always extract and reference relevant details directly from the context. Do not infer or assume anything that is not explicitly stated in the provided content.

                If the relevant answer for a technical query is not present in the context, conversationally state that the information is not available in the provided context.

                Context:
                {context}

                Question:
                {question}

                Answer:"""
            )
        )

    def invoke(self, context: str, question: str) -> Dict[str, Any]:

        if not context or not question:
            logger.error("Context or question is empty.")
            return {"error": "Context and question must be provided."}

        try:
            # Create the chain by combining the prompt and the structured LLM
            chain = self.prompt_template | self.llm
            logger.info("Invoking analysis chain...")
            # Run the chain with the provided RFP text
            response = chain.invoke({"context": context, "question": question})
            # The response should be the Pydantic object ChecklistReport
            logger.info("Successfully received structured response from Google model.")
            print(response)
            return response.content  # Convert Pydantic model to dictionary

        except Exception as e:
            logger.exception(f"Error invoking checklist agent with Google model: {e}")
            return {
                "error": f"Failed to generate checklist using Google model. Error: {str(e)}"
            }


if __name__ == "__main__":
    # Example usage
    agent = RAGAgent()
    context = "This is a sample context for the RFP."
    question = "What are the key requirements?"
    result = agent.invoke(context, question)
    print(result)
