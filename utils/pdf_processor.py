import base64
import os
import PyPDF2
from typing import Tuple
import logging
import pdfplumber

class PDFProcessor:
    def __init__(self, upload_dir="static/uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def base64_to_pdf(self, base64_string: str, filename: str) -> str:
        """Convert base64 string to PDF file"""
        try:
            # Remove data URL prefix if present
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]
            
            # Decode base64
            pdf_bytes = base64.b64decode(base64_string)
            
            # Save to file
            file_path = os.path.join(self.upload_dir, filename)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)
            
            return file_path
            
        except Exception as e:
            logging.error(f"Error converting base64 to PDF: {e}")
            raise e
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, dict]:
        """Extract text and metadata from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                metadata = {
                    "total_pages": len(pdf_reader.pages),
                    "title": pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    "author": pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    "creation_date": pdf_reader.metadata.get('/CreationDate', '') if pdf_reader.metadata else ''
                }
                
                # Extract text from all pages
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    full_text += f"\n--- PAGE {page_num + 1} ---\n"
                    full_text += page_text + "\n"
                
                return full_text, metadata
                
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {e}")
            raise e
    
    def validate_pdf_file(self, file_path: str) -> dict[str, bool]:
        """Validate PDF file basic properties"""
        validation_result = {
            "is_valid_pdf": False,
            "is_readable": False,
            "has_text": False,
            "page_count_valid": False
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                validation_result["is_valid_pdf"] = True
                
                # Check if readable
                if len(pdf_reader.pages) > 0:
                    validation_result["is_readable"] = True
                
                # Check if has extractable text
                first_page_text = pdf_reader.pages[0].extract_text()
                if len(first_page_text.strip()) > 100:
                    validation_result["has_text"] = True
                
                # Check page count (minimum for thesis)
                if len(pdf_reader.pages) >= 50:
                    validation_result["page_count_valid"] = True
                    
        except Exception as e:
            logging.error(f"PDF validation error: {e}")
        
        return validation_result
    
    def detect_page_number_positions(self, file_path):
        positions = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text_objs = page.extract_words()
                # Cari angka di bagian bawah halaman
                for obj in text_objs:
                    if obj['text'].isdigit():
                        # Cek posisi Y (bawah), dan X (kiri/tengah/kanan)
                        y = obj['bottom']
                        x = obj['x0']
                        width = page.width
                        height = page.height
                        if y > height * 0.9:  # bawah
                            if x < width * 0.3:
                                pos = "bottom-left"
                            elif x > width * 0.7:
                                pos = "bottom-right"
                            else:
                                pos = "bottom-center"
                            positions.append({"page": i+1, "position": pos, "number": obj['text']})
        return positions