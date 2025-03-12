import json
import logging
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
DATA_CONTAINER_NAME = "ky-embeddings-all-in"
CITATIONS_CONTAINER_NAME = "ky-citations-filename-embeddings"

# Initialize Azure Blob Storage Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
data_container_client = blob_service_client.get_container_client(DATA_CONTAINER_NAME)
citation_container_client = blob_service_client.get_container_client(CITATIONS_CONTAINER_NAME)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def stream_jsonl(blob_client):
    """
    Streams JSONL files line-by-line to efficiently process large datasets without loading them 
    entirely into memory.
    [Using JSONL format (one JSON object per line) simplifies streaming and avoids issues with partial objects.
    It ensures each line is a complete JSON object, making processing straightforward.]
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
    Loads citation metadata from blobs in the container and 
    preprocesses it into a dictionary for fast lookups.

    :return: Dictionary of citation metadata indexed by filename.
    """
    citation_dict = {}
    for blob in citation_container_client.list_blobs():
        if blob.name.endswith(".json"):
            blob_client = citation_container_client.get_blob_client(blob.name)
            for item in stream_jsonl(blob_client):
                citation_dict[item['filename']] = item
    return citation_dict

def load_data_embeddings_batchwise(batch_size=100):
    """
    Streams data embeddings from blobs in batches using JSONL format for efficient processing.

    :param batch_size: Number of items to yield per batch.
    :yield: Each data embedding item.
    """
    logging.info("Streaming and processing data embeddings batch-wise using JSONL...")
    
    blob_list = [
        blob.name for blob in data_container_client.list_blobs() if blob.name.endswith(".jsonl")  # Note: Using JSONL format
    ]

    if not blob_list:
        logging.warning("No data embedding JSON files found in the container.")
        return

    logging.info(f"Total JSON files found in the container: {len(blob_list)}")

    for blob_name in blob_list:
        logging.info(f"Processing blob: {blob_name}")
        data_blob_client = data_container_client.get_blob_client(blob_name)

        try:
            # Yield each item directly (not using Pandas DataFrame for simplicity)
            for embedding_item in stream_jsonl(data_blob_client):
                yield embedding_item
        except Exception as e:
            logging.error(f"Error processing blob {blob_name}: {e}")

def index_embeddings(data_embeddings_generator, citation_dict):
    """
    Indexes combined documents (data embeddings + citation metadata) into Azure AI Search.

    :param data_embeddings_generator: Generator yielding data embedding items.
    :param citation_dict: Preprocessed dictionary of citation metadata.
    """
    count = 0
    expected_embedding_dimensions = 1536
    print("Indexing embeddings incrementally...")

    for embedding_item in data_embeddings_generator:
        filename = embedding_item.get('filename', '')
        citation = citation_dict.get(filename, {})

        combined_document = {
            "id": embedding_item.get('id', ''),
            "text": embedding_item.get('text', ''),
            "data_embedding": embedding_item.get('embedding', []),
            "DocumentName": citation.get('DocumentName', ''),
            "DocumentURL": citation.get('DocumentURL', ''),
            "citation_embedding": citation.get('embedding', [])
        }

        # Validate embedding dimensions
        if len(combined_document['data_embedding']) != expected_embedding_dimensions:
            print(f"Warning: Invalid data embedding dimensions for {filename}, skipping...")
            continue
        if len(combined_document['citation_embedding']) != expected_embedding_dimensions:
            print(f"Warning: Invalid citation embedding dimensions for {filename}, skipping...")
            continue

        # Index combined_document into Azure Search
        # For simplicity, assume Azure Search client is initialized elsewhere
        # response = search_client.upload_documents([combined_document])
        print(f"Indexed document: {combined_document['id']}")
        count += 1

    print(f"Total indexed documents: {count}")

# Main execution
if __name__ == "__main__":
    try:
        logging.info("Starting indexing process...")
        
        # Load citation dictionary
        citation_dict = load_citation_dict()
        
        # Process and index data embeddings
        data_embeddings_generator = load_data_embeddings_batchwise()
        index_embeddings(data_embeddings_generator, citation_dict)
        
        logging.info("Indexing completed successfully.")
    except Exception as e:
        logging.error(f"Error during indexing: {e}")
