import json
import logging
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CITATIONS_CONTAINER_NAME = "ky-citations-filename-embeddings"

# Initialize Azure Blob Storage Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
citation_container_client = blob_service_client.get_container_client(CITATIONS_CONTAINER_NAME)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def stream_jsonl(blob_client):
    """
    Streams JSONL files line-by-line to efficiently process large datasets without loading them entirely into memory.

    :param blob_client: Azure Blob Storage client for the JSONL file.
    :yield: Each JSON object in the file.
    """
    stream = blob_client.download_blob().chunks()
    buffer = ""
    for chunk in stream:
        buffer += chunk.decode('utf-8')
        lines = buffer.split('\n')
        buffer = lines.pop()  # Keep incomplete line for next chunk
        for line in lines:
            if line.strip():
                yield json.loads(line)

def load_citation_dict():
    """
    Loads citation metadata from blobs in the container and preprocesses it into a dictionary for fast lookups.

    :return: Dictionary of citation metadata indexed by filename.
    """
    citation_dict = {}
    for blob in citation_container_client.list_blobs():
        if blob.name.endswith(".json"):
            blob_client = citation_container_client.get_blob_client(blob.name)
            for item in stream_jsonl(blob_client):
                citation_dict[item['filename']] = item
    return citation_dict

# Test run
if __name__ == "__main__":
    try:
        logging.info("Starting citation embeddings loading test...")
        citation_dict = load_citation_dict()
        logging.info("Citation embeddings successfully loaded.")
    except Exception as e:
        logging.error(f"Error during citation embeddings loading: {e}")
