import os
import requests
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING = "your_connection_string"
BLOB_CONTAINER_NAME = "filings-documents"

# Base URL for filings
BASE_URL = "https://abc.com"

# Function to initialize Azure Blob Storage container
def initialize_blob_storage():
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    try:
        container_client = blob_service_client.create_container(BLOB_CONTAINER_NAME)
        print(f"Container '{BLOB_CONTAINER_NAME}' created.")
    except Exception as e:
        print(f"Container '{BLOB_CONTAINER_NAME}' already exists.")
    return blob_service_client

# Function to upload file to Azure Blob Storage
def upload_to_blob_storage(blob_service_client, local_file_path, blob_name):
    try:
        blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=blob_name)
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"Uploaded {blob_name} to Blob Storage.")
    except Exception as e:
        print(f"Failed to upload {blob_name} to Blob Storage: {e}")

# Function to scrape and download documents
def scrape_and_download_documents():
    # Filing URL
    filing_url = "https://abc.com"

    # Send GET request
    response = requests.get(filing_url)
    if response.status_code != 200:
        print("Failed to fetch the webpage.")
        return

    # Parse HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all filing entries (assumed anchor tags within a specific class or ID)
    document_links = soup.find_all("a", href=True, text=True)  # Adjust based on actual structure

    # Create a directory to save downloaded files
    os.makedirs("downloads", exist_ok=True)

    # Initialize Blob Storage
    blob_service_client = initialize_blob_storage()

    for link in document_links:
        if "Filing" in link.text:  # Adjust to filter specific links by text or attribute
            document_url = BASE_URL + link['href']
            file_name = link.text.strip() + ".pdf"

            # Download the document
            try:
                print(f"Downloading {file_name} from {document_url}...")
                doc_response = requests.get(document_url, stream=True)
                if doc_response.status_code == 200:
                    local_file_path = os.path.join("downloads", file_name)
                    with open(local_file_path, "wb") as file:
                        for chunk in doc_response.iter_content(chunk_size=1024):
                            file.write(chunk)
                    print(f"Downloaded {file_name}.")

                    # Upload to Azure Blob Storage
                    upload_to_blob_storage(blob_service_client, local_file_path, file_name)

                    # Clean up local file after upload
                    os.remove(local_file_path)
                else:
                    print(f"Failed to download {file_name}. HTTP Status Code: {doc_response.status_code}")
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")

if __name__ == "__main__":
    scrape_and_download_documents()
