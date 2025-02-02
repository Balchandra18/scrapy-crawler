# Ensure destination container exists, or create it
try:
    if not dest_container.exists():
        dest_container.create_container()
    else:
        print(f"Container '{DEST_CONTAINER_NAME}' already exists. Overwriting existing blobs...")
        for blob in dest_container.list_blobs():
            dest_container.get_blob_client(blob).delete_blob()
except Exception as e:
    print(f"Error handling destination container: {e}")



from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from azure.storage.blob import BlobServiceClient
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Storage and OpenAI credentials
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
SOURCE_CONTAINER_NAME = os.getenv("SOURCE_CONTAINER_NAME")
DEST_CONTAINER_NAME = os.getenv("DEST_CONTAINER_NAME")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ID")

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

# Define OpenAI client
from openai import AzureOpenAI
client = AzureOpenAI(api_key=AZURE_OPENAI_KEY, azure_endpoint=AZURE_OPENAI_ENDPOINT)

# Function to extract text from PDF
def get_pdf_text(blob_client):
    pdf_text = ""
    stream = blob_client.download_blob()
    reader = PdfReader(stream.readall())
    for page in reader.pages:
        pdf_text += page.extract_text() + " "
    return pdf_text.strip()

# Function to split text into chunks
def get_chunks(text, chunk_length=500):
    chunks = []
    while len(text) > chunk_length:
        last_period_index = text[:chunk_length].rfind('.')
        if last_period_index == -1:
            last_period_index = chunk_length
        chunks.append(text[:last_period_index])
        text = text[last_period_index+1:]
    chunks.append(text)
    return chunks

# Function to create embeddings
def create_embeddings(text):
    return client.embeddings.create(input=[text], model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ID).data[0].embedding

# Function to process PDFs, generate embeddings, and store results
def process_pdfs():
    source_container = blob_service_client.get_container_client(SOURCE_CONTAINER_NAME)
    dest_container = blob_service_client.get_container_client(DEST_CONTAINER_NAME)
    dest_container.create_container()

    embeddings_data = []
    for blob in source_container.list_blobs():
        if not blob.name.endswith(".pdf"):
            print(f"Skipping non-PDF file: {blob.name}")
            continue
        
        print(f"Processing {blob.name}...")
        blob_client = source_container.get_blob_client(blob)
        text = get_pdf_text(blob_client)
        chunks = get_chunks(text)
        
        for i, chunk in enumerate(chunks):
            embeddings_data.append({
                "id": f"{blob.name}_{i}",
                "filename": blob.name,
                "text": chunk,
                "embedding": create_embeddings(chunk)
            })
    
    # Save embeddings data to JSON
    json_data = json.dumps(embeddings_data)
    dest_blob_client = dest_container.get_blob_client("docVectors_azure.json")
    dest_blob_client.upload_blob(json_data, overwrite=True)
    print("Embeddings stored successfully.")

# Run the processing function
process_pdfs()
