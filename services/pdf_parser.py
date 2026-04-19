import pdfplumber
import io

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """
        Takes raw PDF bytes (from a FastAPI upload) and extracts the text.
        """
        text_content = []
        
        # We use io.BytesIO to treat the raw bytes like a physical file
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text_content.append(extracted_text)
                    
        # Join all pages with a newline separator
        full_text = "\n".join(text_content)
        return full_text.strip()