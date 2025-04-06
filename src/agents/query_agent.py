from pinecone import Pinecone
import constants
import textwrap
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import os
from langchain.memory import ConversationBufferMemory


class QueryAgent:
    """Agent jo database ko query karega and relevant results return karega"""

    def __init__(self):
        """Initialize karo QueryAgent class ko"""

        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index("rfp-agent")

        # self.llm = ChatGoogleGenerativeAI(
        #     model=constants.QUERY_AGENT_MODEL,
        #     temperature=0.8,
        #     max_tokens=None,
        #     timeout=None,
        #     max_retries=2,
        # ).with_structured_output(QueryOutputFormat)

    # def choose_query_and_namespace(self, user_query) -> tuple[list[str], list[str]]:
    #     """User query ke hisaab se namespace choose karo and query ko modify karo"""

    #     system_prompt = textwrap.dedent(constants.QUERY_AGENT_SYSTEM_PROMPT).strip()

    #     messages = [
    #         ("system", system_prompt),
    #         ("user", "\nUser query: " + user_query),
    #     ]

    #     result = self.llm.invoke(messages)

    #     return (result.queries, result.namespaces)

    def query_database(self, query, namespace, top_k):
        """Database ko query karega and top_k results return karega"""

        query_embedding = self.pc.inference.embed(
            model=constants.PINECONE_EMBEDDING_MODEL,
            inputs=[query],
            parameters={"input_type": "query"},
        )

        intermediate_results = self.index.query(
            namespace=namespace,
            vector=query_embedding[0].values,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
        )

        if not intermediate_results["matches"]:
            return "No relevant data found"

        reranked_results = self.pc.inference.rerank(
            model=constants.PINECONE_RERANKER_MODEL,
            query=query,
            documents=[
                match["metadata"]["text"] for match in intermediate_results["matches"]
            ],
            top_n=top_k,
            return_documents=True,
            parameters={"truncate": "END"},
        )

        retrieved_results = [item["document"]["text"] for item in reranked_results.data]

        retrieved_results_str = "---\n" + query + "\n"
        retrieved_results_str += "\n".join(retrieved_results)
        retrieved_results_str += "\n---\n"

        return retrieved_results_str

    def retrieve_relevant_data(self, user_query, namespace):
        """User query ke hisaab se relevant data retrieve karega"""

        # queries, namespaces = self.choose_query_and_namespace(user_query)

        retrieved_data = []

        # for query, namespace in zip(queries, namespaces):
        retrieved_data.append(self.query_database(user_query, namespace, 10))

        return retrieved_data
