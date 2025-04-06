from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from pydantic import BaseModel

load_dotenv()


class LinksFormat(BaseModel):
    links: list[str]


def get_references(context: str):

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Share me all the links related articles, news, etc related to the RPF below.--\n"
        + context,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearchRetrieval)]
        ),
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Structure the links in a list format with its components as links. {response}",
        config={
            "response_mime_type": "application/json",
            "response_schema": LinksFormat,
        },
    )

    # print(response.parsed.links)

    return response.parsed.links


if __name__ == "__main__":
    context = (
        "RPF: The RPF is a document that outlines the requirements and expectations for a project or initiative. "
        "It serves as a guide for stakeholders to understand the project's goals, objectives, and deliverables. "
        "The RPF should include information such as the project's scope, timeline, budget, and resources needed. "
        "It should also outline the roles and responsibilities of team members and stakeholders."
    )
    print(get_references(context))
