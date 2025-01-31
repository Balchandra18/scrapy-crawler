import os
import json
from azure.storage.blob import BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, VectorSearch, VectorSearchProfile, HnswParameters
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import openai
import tiktoken

# Azure Configurations
AZURE_BLOB_CONNECTION_STRING = "your_azure_blob_connection_string"
AZURE_BLOB_CONTAINER_NAME = "your_container_name"
AZURE_SEARCH_ENDPOINT = "your_azure_search_endpoint"
AZURE_SEARCH_KEY = "your_azure_search_key"
AZURE_SEARCH_INDEX_NAME = "your_index_name"
AZURE_OPENAI_API_KEY = "your_openai_api_key"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

# Initialize OpenAI API
openai.api_key = AZURE_OPENAI_API_KEY

# Initialize Azure Blob Storage Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER_NAME)

# Initialize Azure AI Search Client
search_client = SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX_NAME, AzureKeyCredential(AZURE_SEARCH_KEY))
index_client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, AzureKeyCredential(AZURE_SEARCH_KEY))


# Function to Read PDFs from Azure Blob Storage
def read_pdfs_from_blob():
    pdf_texts = []
    blob_list = container_client.list_blobs()

    for blob in blob_list:
        if blob.name.endswith(".pdf"):
            blob_client = container_client.get_blob_client(blob.name)
            pdf_bytes = blob_client.download_blob().readall()

            reader = PdfReader(pdf_bytes)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            pdf_texts.append((blob.name, text))

    return pdf_texts


# Function to Chunk Text
def chunk_text(text, chunk_size=500, overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return text_splitter.split_text(text)


# Function to Generate Embeddings using OpenAI
def get_embedding(text):
    response = openai.embeddings.create(input=[text], model="text-embedding-ada-002")
    return response["data"][0]["embedding"]


# Function to Index Data into Azure AI Search
def index_documents():
    pdf_texts = read_pdfs_from_blob()
    documents = []

    for doc_name, text in pdf_texts:
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            doc_id = f"{doc_name}_{i}"
            documents.append({
                "id": doc_id,
                "content": chunk,
                "vector": embedding
            })

    search_client.upload_documents(documents)


# Function to Create an Azure AI Search Index
def create_search_index():
    fields = [
        SimpleField(name="id", type="Edm.String", key=True),
        SearchableField(name="content", type="Edm.String"),
        SearchableField(name="vector", type="Collection(Edm.Single)", filterable=True, sortable=False, facetable=False)
    ]
    
    vector_search = VectorSearch(
        algorithms=[HnswParameters(name="defaultHnsw")],
        profiles=[VectorSearchProfile(name="default", algorithm="defaultHnsw")]
    )

    index = SearchIndex(name=AZURE_SEARCH_INDEX_NAME, fields=fields, vector_search=vector_search)
    index_client.create_or_update_index(index)


# Function to Perform Vector Search in Azure AI Search
def search_similar_docs(query):
    query_embedding = get_embedding(query)

    results = search_client.search(
        search_text="",
        vector_queries=[{
            "vector": query_embedding,
            "k": 3,
            "fields": ["vector"]
        }],
        select=["content"]
    )

    return [result["content"] for result in results]


# Function to Generate Response using GPT-4o
def generate_response(query):
    relevant_chunks = search_similar_docs(query)
    context = "\n\n".join(relevant_chunks)

    prompt = f"Use the following context to answer the query:\n{context}\n\nQuery: {query}\n\nAnswer:"
    response = openai.ChatCompletion.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "system", "content": "You are an AI assistant helping with document retrieval."},
                  {"role": "user", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"]


# Main Execution
if __name__ == "__main__":
    create_search_index()  # Create index
    index_documents()  # Index documents
    while True:
        query = input("Ask a question: ")
        if query.lower() in ["exit", "quit"]:
            break
        answer = generate_response(query)
        print("AI Response:", answer)
