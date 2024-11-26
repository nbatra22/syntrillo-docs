import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import BedrockEmbeddings
import boto3


def initialize_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name='us-east-1'
    )


def initialize_db(collection_name):
    bedrock = initialize_bedrock_client()
    bedrock_embeddings = BedrockEmbeddings(model_id="cohere.embed-english-v3", client=bedrock)
    persistent_client = chromadb.PersistentClient()

    return Chroma(
        client=persistent_client,
        collection_name=collection_name,
        embedding_function=bedrock_embeddings,
    )

def get_similar_docs(db, query, k=10, score=True):
    return db.similarity_search_with_score(query, k=k) if score else []
