import os
from azure.storage.blob import BlobServiceClient
from llama_index import GPTSimpleVectorIndex, Document
from llama_index.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores import SimpleVectorStore
from azure.ai.search import SearchClient
from azure.core.credentials import AzureKeyCredential

# Define environment variables for PromptFlow
AZURE_BLOB_CONNECTION_STRING = os.environ.get("AZURE_BLOB_CONNECTION_STRING")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME")
BLOB_CONTAINER_NAME = os.environ.get("BLOB_CONTAINER_NAME")

def download_files_from_blob(container_name, download_path):
    """Download files from Azure Blob Storage."""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(container_name)
    
    os.makedirs(download_path, exist_ok=True)
    for blob in container_client.list_blobs():
        if blob.name.endswith((".pdf", ".docx", ".txt")):
            file_path = os.path.join(download_path, blob.name)
            with open(file_path, "wb") as file:
                file.write(container_client.download_blob(blob.name).readall())
    print(f"Downloaded files to {download_path}")

def chunk_document(content, max_tokens=500):
    """Chunk documents while preserving context."""
    from llama_index.text_splitter import TokenTextSplitter

    splitter = TokenTextSplitter(chunk_size=max_tokens, chunk_overlap=100)
    return splitter.split_text(content)

def create_embeddings_and_index(files_dir):
    """Create embeddings and an index using LlamaIndex."""
    documents = []
    
    for file_name in os.listdir(files_dir):
        file_path = os.path.join(files_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            chunks = chunk_document(content)
            for chunk in chunks:
                documents.append(Document(chunk))
    
    embedding_model = OpenAIEmbedding(
        engine="text-embedding-ada-002",
        api_key=AZURE_OPENAI_KEY,
        api_base=AZURE_OPENAI_ENDPOINT
    )
    vector_store = SimpleVectorStore()
    index = GPTSimpleVectorIndex(documents, embedding_model=embedding_model, vector_store=vector_store)
    index.save_to_disk("index.json")
    print("Index created and saved.")
    return index

def upload_index_to_azure_search(index_file):
    """Upload index data to Azure Cognitive Search."""
    search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=AZURE_SEARCH_INDEX_NAME, credential=AzureKeyCredential(AZURE_SEARCH_KEY))
    
    with open(index_file, "r", encoding="utf-8") as file:
        index_data = file.read()
    
    documents = [{"id": str(i), "content": chunk} for i, chunk in enumerate(index_data.split("\n\n"))]
    result = search_client.upload_documents(documents)
    print(f"Uploaded index to Azure Search: {result}")

def main():
    download_path = "./downloaded_documents"
    download_files_from_blob(BLOB_CONTAINER_NAME, download_path)
    create_embeddings_and_index(download_path)
    upload_index_to_azure_search("index.json")

if __name__ == "__main__":
    main()
