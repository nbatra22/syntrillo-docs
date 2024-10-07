import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import Chroma

# Set up Bedrock client
import boto3

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # Replace with your preferred region
)

# Initialize Bedrock embeddings
embeddings = BedrockEmbeddings(
    client=bedrock_runtime,
    model_id="amazon.titan-embed-text-v1"
)

# Load PDF
pdf_path = "path/to/your/document.pdf"
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)
texts = text_splitter.split_documents(documents)

# Create and store embeddings in ChromaDB

# Persist the database to disk
db.persist()

print(f"Embeddings created and stored for {len(texts)} text chunks")

# Example of how to query the database
query = "Your query here"
results = db.similarity_search(query)
print(f"Top relevant chunk: {results[0].page_content}")