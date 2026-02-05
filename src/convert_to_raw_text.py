import base64
import os

from docx import Document
import fitz
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_file(file_path: str, file_extension: str) -> str:
    try:
        ext = file_extension.lower()

        if ext == "docx":
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        elif ext == "pdf":
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text

        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext in ("png", "jpg", "jpeg"):
            with open(file_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Extract all revelvant to studying notes readable text from this image. Only output the notes, no other text(such as sure! here are the notes)",
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/{ext};base64,{image_b64}",
                            },
                        ],
                    }
                ],
            )

            return response.output_text

        else:
            return f"Unsupported file type: {file_extension}"

    except Exception as e:
        return f"Error extracting text: {e}"
