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

data_ingestor = DataIngestor()
query_agent = QueryAgent()


def get_conversational_chain(context, question):
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-exp-03-25",
        client=genai,
        temperature=0.3,
    )
    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    ans = model.invoke(
        input=prompt.format(context=f"{context}", question=f"{question}"),
        # messages=[
        #     {
        #         "role": "user",
        #         "content": prompt.format(context=f"{context}", question=f"{question}"),
        #     }
        # ],
    )
    return ans


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "upload some pdfs and ask me a question"}
    ]


def user_input(user_question):
    """User se input le raha hai"""

    ref = query_agent.retrieve_relevant_data(user_question, "test")
    from langchain.schema import Document

    ref = [Document(page_content=d, metadata={}) for d in ref]

    ans = get_conversational_chain(ref, user_question)

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
                for item in response["output_text"]:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        if response is not None:
            message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)


if __name__ == "__main__":
    main()
