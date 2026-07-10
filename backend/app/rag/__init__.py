"""RAG pipeline for CareerVerse AI.

Public surface
--------------
from app.rag.embeddings  import chunk_text, generate_embedding, generate_embeddings
from app.rag.store       import (get_collection, add_documents, delete_documents,
                                  query, index_job_description,
                                  ChromaDBError, EmptyCollectionError)
from app.rag.retriever   import retrieve_relevant_job_descriptions, EmbeddingError
"""
