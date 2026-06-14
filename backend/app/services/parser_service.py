import os
import logging
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class ParserService:
    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from a PDF file page by page.
        Returns a list of dicts with page_number (1-indexed) and extracted text.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"PDF file not found at {file_path}")
            
        logger.info(f"Starting PDF extraction for {file_path}")
        reader = PdfReader(file_path)
        pages_content = []
        
        for idx, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text and text.strip():
                    pages_content.append({
                        "page_number": idx + 1,
                        "text": text.strip()
                    })
            except Exception as e:
                logger.warning(f"Failed to extract text from page {idx + 1}: {e}")
                
        logger.info(f"Successfully extracted {len(pages_content)} pages from {file_path}")
        return pages_content

    @staticmethod
    def chunk_text(pages_content: List[Dict[str, Any]], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Splits page text into smaller, overlapping chunks while maintaining association with page numbers.
        """
        chunks = []
        for page_data in pages_content:
            page_num = page_data["page_number"]
            text = page_data["text"]
            
            text_len = len(text)
            if text_len <= chunk_size:
                chunks.append({
                    "page_number": page_num,
                    "text": text
                })
                continue
                
            start = 0
            while start < text_len:
                end = start + chunk_size
                chunk_content = text[start:end]
                chunks.append({
                    "page_number": page_num,
                    "text": chunk_content
                })
                start += (chunk_size - chunk_overlap)
                
        logger.info(f"Generated {len(chunks)} chunks from document pages")
        return chunks
