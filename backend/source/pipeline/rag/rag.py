import faiss
import numpy as np
import os
import logging
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from enum import Enum
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAG:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', index_path: str = 'code_index.faiss'):
        logger.info("Initializing RAG")
        self.model: SentenceTransformer = SentenceTransformer(model_name)
        self.index_path: str = index_path
        self.index: Optional[faiss.Index] = None
        self.code_chunks: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        logger.debug(f"Model name: {model_name}, Index path: {index_path}")

        # initializes faiss index if not found then must be first run
        if not self.index_path or not os.path.exists(self.index_path):
            logger.debug("No existing index found, will create new index")
            self.index = None
        else:
            try:
                logger.debug(f"Loading existing index from {self.index_path}")
                self.index = faiss.read_index(self.index_path)
                logger.info("Successfully loaded existing index")
            except Exception as e:
                logger.warning(f"Could not load index from {self.index_path}. Creating new index. Error: {str(e)}")
                self.index = None

    def extract_content(self, file_path: str) -> Dict[str, str]:
        logger.debug(f"Extracting content from {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                filename = os.path.basename(file_path)
                content = f.read()
            logger.debug(f"Successfully extracted content from {filename}")
            return {
                "filename": filename,
                "content": content
            }
        except Exception as e:
            logger.warning(f"Could not process file {file_path}: {str(e)}")
            return {"filename": "", "content": ""}

    def embed_code(self, code_files: List[Dict[str, str]]) -> None:
        logger.info(f"Starting code embedding process for {len(code_files)} files")
        code_chunks = []
        metadata = []

        # Process each dictionary of code content
        for file_dict in code_files:
            try:
                content = file_dict['content']
                filename = file_dict['filename']
                logger.debug(f"Processing file: {filename}")

                # get the language of the file
                language = os.path.splitext(filename)[1][1:].upper() if os.path.splitext(filename)[1] else "TXT"
                logger.debug(f"Detected language: {language}")
                
                # split into meaningful chunks
                chunks = self._split_into_chunks(content, language)
                code_chunks.extend(chunks)
                logger.debug(f"Created {len(chunks)} chunks for {filename}")
                
                # store metadata for each chunk
                for i, chunk in enumerate(chunks):
                    metadata.append({
                        'file_name': filename,
                        'chunk_number': i,
                        'start_line': i * 10,
                    })
            except Exception as e:
                logger.warning(f"Could not process file {filename}: {str(e)}")
                continue

        if not code_chunks:
            logger.error("No valid code chunks were extracted from the files")
            raise ValueError("No valid code chunks were extracted from the files.")

        self.code_chunks = code_chunks
        self.metadata = metadata
        logger.info(f"Total chunks created: {len(code_chunks)}")
        
        # create embeddings for each chunk
        logger.info("Creating embeddings for chunks")
        embeddings = self.model.encode(code_chunks, show_progress_bar=True)
        logger.debug(f"Created embeddings with shape: {embeddings.shape}")

        # initialize or update faiss index
        if self.index is None:
            logger.debug("Initializing new FAISS index")
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(np.array(embeddings))
        logger.debug(f"Added {len(embeddings)} embeddings to index")
        
        # save index
        logger.info(f"Saving index to {self.index_path}")
        faiss.write_index(self.index, self.index_path)
        logger.info("Index saved successfully")

    def _split_into_chunks(self, content: str, lang: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        logger.debug(f"Starting content splitting with lang={lang}, chunk_size={chunk_size}, overlap={overlap}")
        # error catching
        if not content:
            logger.error("Empty content provided")
            raise ValueError("Content cannot be empty")
        if not isinstance(content, str):
            logger.error(f"Invalid content type: {type(content)}")
            raise TypeError("Content must be a string")
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            logger.error(f"Invalid chunk_size: {chunk_size}")
            raise ValueError("chunk_size must be a positive integer")
        if not isinstance(overlap, int) or overlap < 0:
            logger.error(f"Invalid overlap: {overlap}")
            raise ValueError("overlap must be a non-negative integer")
        if overlap >= chunk_size:
            logger.error(f"Overlap ({overlap}) greater than or equal to chunk_size ({chunk_size})")
            raise ValueError("overlap must be less than chunk_size")
        
        chunks = []
        
        try:
            # validate if language is supported
            try:
                logger.debug(f"Attempting to validate language: {lang}")
                language_enum = Language[lang]
                logger.debug(f"Language {lang} is supported")
            except KeyError:
                # fallback to generic text splitting if language not supported
                logger.warning(f"Language '{lang}' not supported. Falling back to generic text splitting.")
                language_enum = None

            # create the splitter with language-specific settings
            logger.debug("Creating text splitter")
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language_enum,
                chunk_size=chunk_size,
                chunk_overlap=overlap
            ) if language_enum else RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False
            )
            
            # split the content into chunks
            logger.debug("Splitting content into chunks")
            code_docs = splitter.create_documents([content])
            chunks = [doc.page_content for doc in code_docs]
            if not chunks:
                logger.error("No chunks generated from content")
                raise ValueError("Failed to generate chunks from the content")
            
            logger.info(f"Successfully split content into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error splitting content into chunks: {str(e)}")
            raise RuntimeError(f"Error splitting content into chunks: {str(e)}")


    def retrieve_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        logger.debug(f"Starting context retrieval for query with k={k}")
        if self.index is None or self.index.ntotal == 0:
            logger.error("Attempted to query empty Faiss index")
            raise ValueError("The Faiss index is empty. Please embed code before querying.")

        logger.debug("Encoding query")
        query_embedding = self.model.encode([query])
        logger.debug("Searching index")
        distances, indices = self.index.search(np.array(query_embedding), k)

        results = []
        logger.debug(f"Processing {len(indices[0])} search results")
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.code_chunks):
                results.append({
                    'code': self.code_chunks[idx],
                    'metadata': self.metadata[idx],
                    'similarity_score': float(1 / (1 + distances[0][i]))
                })
                logger.debug(f"Added result {i+1} with similarity score {float(1 / (1 + distances[0][i]))}")
            else:
                logger.warning(f"Skipping invalid index {idx}")

        if not results:
            logger.error("No relevant context found in search results")
            raise ValueError("No relevant context found. The index may not be populated correctly.")

        logger.info(f"Successfully retrieved {len(results)} context results")
        return results

    def clear_index(self) -> None:
        logger.info("Clearing index")
        self.index = faiss.IndexFlatL2(384)
        self.code_chunks = []
        self.metadata = []
        logger.debug("Writing empty index to disk")
        faiss.write_index(self.index, self.index_path)
        logger.info("Index cleared successfully")
