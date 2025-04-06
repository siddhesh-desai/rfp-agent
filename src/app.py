import os

# # from PyPDF2 import PdfReader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
import streamlit as st
import google.generativeai as genai

# from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from main import QueryAgent

load_dotenv()
# os.getenv("GEMINI_API_KEY")
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# read all pdf files and return text

from PDFIngestor.PDFIngestor import DataIngestor
from agents.rag_agent import RAGAgent

data_ingestor = DataIngestor()
query_agent = QueryAgent()


def use_rag_agent(question: str) -> str:
    """Uses the RAG agent to analyze the context and answer the question."""
    query_agent = QueryAgent()
    context = query_agent.retrieve_relevant_data(user_query=question, namespace="test")

    context = context = "\n\n".join(context)
    if context == "No relevant data found":
        return context

    rag_agent = RAGAgent()
    response = rag_agent.invoke(context, question)

    return response


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "upload some pdfs and ask me a question"}
    ]


def user_input(user_question):
    """User se input le raha hai"""

    ans = use_rag_agent(user_question)

    # response = chain(
    #     {"input_documents": ref, "question": user_question},
    #     return_only_outputs=True,
    # )

    print(ans)
    return ans


def main():
    st.set_page_config(page_title="Gemini PDF Chatbot", page_icon="🤖")

    # Sidebar for uploading PDF files
    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader(
            "Upload your PDF Files and Click on the Submit & Process Button",
            accept_multiple_files=True,
        )
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                uploaded_file = pdf_docs[0]  # your UploadedFile object

                # Save to a temp location (e.g., inside a temp_files/ folder)
                save_dir = "temp_files"
                os.makedirs(save_dir, exist_ok=True)

                save_path = os.path.join(save_dir, uploaded_file.name)

                # Write the file content
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.read())

                # Now you can get the absolute path
                abs_path = os.path.abspath(save_path)
                print(abs_path)

                # print(pdf_docs[0])
                # pdf_docs[0] = os.path.abspath(pdf_docs[0])
                # print(pdf_docs[0])
                raw_text = data_ingestor.ingest_pdf(abs_path, "rfp-agent", "test")
                st.success("Done")

    # Main content area for displaying chat messages
    st.title("Chat with PDF files using Gemini🤖")
    st.write("Welcome to the chat!")
    st.sidebar.button("Clear Chat History", on_click=clear_chat_history)

    # Chat input
    # Placeholder for chat messages

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "upload some pdfs and ask me a question"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    # Display chat messages and bot response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = user_input(prompt)
                placeholder = st.empty()
                full_response = ""
                # for item in response["output_text"]:
                #     full_response += item
                #     placeholder.markdown(full_response)
                placeholder.markdown(response)
        if response is not None:
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
