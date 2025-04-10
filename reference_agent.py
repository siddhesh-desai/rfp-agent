import os
from typing import Any, List, Dict, Optional, Type

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent

from src.core.logger import logger
from src.OnboardingAgent.utils import (
    PROMPTS,
    INPUT_VARIABLES,
    PARTIAL_VARIABLES,
)

import textwrap


class BaseAgent:
    """Base Agent class that follows ReACT Strategy with access to tools"""

    def __init__(
        self,
        model: str,
        tools: List[Any],
        prompt: str,
        response_format: Type[Any] = None,
    ) -> None:
        """Initializes the BaseAgent with the model, tools, and prompt

        Args:
            model (str): The model to use for the agent
            tools (List[Any]): The tools to use for the agent
            prompt (str): The prompt to use for the agent
        """

        self.tools = tools
        self.prompt = textwrap.dedent(prompt).strip()
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set.")
            raise ValueError("OPENAI_API_KEY environment variable is not set.")

        self.model = ChatOpenAI(model=model, api_key=api_key)

        self.is_structured_output = response_format is not None

        self.agent_executor = create_react_agent(
            self.model,
            self.tools,
            prompt=self.prompt,
            response_format=response_format,
        )

    def invoke(
        self,
        user_input: str,
        access_token: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
        business_id: Optional[str] = None,
    ) -> str:
        """Generates a response from the agent based on the user input and chat history.

        Args:
            user_input (str): The user input to generate the response.
            access_token (Optional[str]): The optional access token for accessing the Qest API tools.
            chat_history (Optional[List[Dict]]): The optional chat history to use for maintaining context across interactions.

        Returns:
            str: The response generated by the agent.
        """

        try:
            chat_history = chat_history or []
            user_input = user_input.strip()
            messages = chat_history + [{"role": "user", "content": user_input}]

            config_ = {"configurable": {"access_token": access_token}}

            if business_id:
                config_["configurable"]["business_id"] = business_id

            logger.info(
                f"Invoking agent executor with config: {config_}\n\n"
            )  # Added logging statement

            response = self.agent_executor.invoke(
                {"messages": messages},
                config={"configurable": {"access_token": access_token}},
            )

            # Collect artifacts
            artifacts = []
            for message in response["messages"]:
                if hasattr(message, "artifact"):
                    artifact = message.artifact
                    if artifact is None:
                        continue
                    if isinstance(artifact, list):
                        artifacts.extend(artifact)
                    else:
                        artifacts.append(artifact)

            if self.is_structured_output:
                return {
                    "content": response["structured_response"],
                    "artifacts": artifacts if artifacts != [] else None,
                    "follow_up_options": None,
                }

            return {
                "content": response["messages"][-1].content,
                "artifacts": artifacts,
                "follow_up_options": None,
            }

        except KeyError as e:
            logger.error("KeyError encountered while processing response: %s", str(e))
            return "An unexpected response format was encountered. Please try again."

        except Exception as e:
            logger.exception("Error occurred while invoking the agent: %s", str(e))
            return "The response was not generated due to an internal error. Please try again later."