                documents.clear()  # Clear batch after upload
            except Exception as e:
                logging.error(f"Error uploading batch: {e}")

    # Upload remaining documents in the final batch
    if documents:
        try:
            response = search_client.upload_documents(documents)
            logging.info(f"Uploaded final batch of {len(documents)} documents.")
            count += len(documents)
        except Exception as e:
            logging.error(f"Error uploading final batch: {e}")

    logging.info(f"Total indexed documents: {count}")


if __name__ == "__main__":
    try:
        logging.info("Starting indexing process...")

        # Load citations and process embeddings
        citation_dict = load_citation_dict()
        data_embeddings_generator = load_data_embeddings_batchwise()

        # Index combined documents
        index_embeddings(data_embeddings_generator, citation_dict)

        logging.info("Indexing completed successfully.")
    except Exception as e:
        logging.error(f"Error during indexing: {e}")
