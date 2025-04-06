from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from docling.chunking import HybridChunker
from langchain_pinecone import PineconeEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
import json
import os
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

import pymupdf  # PyMuPDF
import os


class DataIngestor:
    """Ye data ingest karega from files to Pinecone"""

    def __init__(self):
        """DataIngestor ko Initialise karega"""

        self.embeddings = PineconeEmbeddings(
            model="llama-text-embed-v2",
            pinecone_api_key=os.environ.get("PINECONE_API_KEY"),
            batch_size=32,
            document_params={"input_type": "passage", "truncation": "END"},
        )

        self.pinecone = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    def load_pdf_into_docling_chunks(self, path_to_pdf):
        """PDF ka docling banaega"""

        loader = DoclingLoader(
            file_path=path_to_pdf,
            export_type=ExportType.DOC_CHUNKS,
            chunker=HybridChunker(
                tokenizer="sentence-transformers/all-MiniLM-L6-v2", max_tokens=1024
            ),
        )

        chunks = loader.load()

        for doc in chunks:
            if "dl_meta" in doc.metadata:
                doc.metadata["dl_meta"] = json.dumps(doc.metadata["dl_meta"])

        return chunks

    # def load_pdf_into_docling_chunks(self, path_to_pdf):
    #     """Simple and fast PDF loader with basic chunking"""

    #     # Read PDF text using PyMuPDF
    #     text = ""
    #     with pymupdf.open(path_to_pdf) as doc:
    #         for page in doc:
    #             text += page.get_text()

    #     # Use LangChain's character splitter to chunk the text
    #     splitter = RecursiveCharacterTextSplitter(
    #         chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
    #     )
    #     chunks = splitter.create_documents([text])

    #     return chunks

    def load_chunks_into_pinecone(self, docling_chunks, index_name, namespace):
        """Docling chunks ko Pinecone mein daal dega"""

        existing_indexes = [
            index_info["name"] for index_info in self.pinecone.list_indexes()
        ]

        if index_name not in existing_indexes:
            self.pinecone.create_index(
                name=index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=os.getenv("PINECONE_CLOUD"),
                    region=os.getenv("PINECONE_REGION"),
                ),
            )
            while not self.pinecone.describe_index(index_name).status["ready"]:
                time.sleep(1)

        index = self.pinecone.Index(index_name)

        vectorStore = PineconeVectorStore.from_documents(
            documents=docling_chunks,
            index_name=index_name,
            embedding=self.embeddings,
            namespace=namespace,
        )

        # time.sleep(10)

        print("Index after upsert:")
        print(self.pinecone.Index(index_name).describe_index_stats())
        print("\n")

    def ingest_pdf(self, path_to_pdf, index_name, namespace):
        """PDF ko ingest karega"""

        chunks = self.load_pdf_into_docling_chunks(path_to_pdf)
        self.load_chunks_into_pinecone(chunks, index_name, namespace)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    data_ingestor = DataIngestor()
    data_ingestor.ingest_pdf("files/1.pdf", "rfp-agent", "test")
