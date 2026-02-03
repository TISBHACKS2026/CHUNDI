from docx import Document
import fitz  


def extract_text_from_file(file_path: str, file_extension: str):
    try:
        ext = file_extension.lower()

        if ext == 'docx':
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text

        elif ext == 'pdf':
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text

        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        else:
            return f"Unsupported file type: {file_extension}"

    except Exception as e:
        return f"Error extracting text: {str(e)}"
