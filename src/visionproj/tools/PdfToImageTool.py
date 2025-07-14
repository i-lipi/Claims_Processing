from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import fitz  # PyMuPDF for PDF to Image conversion
import io
import base64
from PIL import Image
import json
import os
# Define the input schema for the tool (PDF path)
class PdfToImageInput(BaseModel):
    pdf_file_path: str = Field(..., description="Path to the PDF file to be converted to images")

# Define the custom PDF-to-image tool
class PdfToImageTool(BaseTool):
    name: str = "pdf_to_image_tool"
    description: str = "Converts each page of a PDF into a base64-encoded image."
    args_schema: Type[BaseModel] = PdfToImageInput  # The input schema for this tool

    def _run(self, pdf_file_path: str) -> str:
        """This method converts the PDF to base64-encoded images."""
        try:
            if not os.path.exists(pdf_file_path):
                raise FileNotFoundError(f"PDF file not found at the path: {pdf_file_path}")

            doc = fitz.open(pdf_file_path)  # Open the PDF file
            images = []
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)  # Get the page
                pix = page.get_pixmap()  # Render the page to a pixmap (image)
                img_bytes = pix.tobytes("png")  # Convert the pixmap to bytes

                # Convert image bytes to base64
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                images.append(img_base64)  # Add the base64 image to the list
                
                # Optionally, save the image to a file (for debugging purposes)
                img = Image.open(io.BytesIO(img_bytes))
                img.save(f"output_page_{page_num + 1}.png", "PNG")
                print(f"Page {page_num + 1} saved as output_page_{page_num + 1}.png")
            
            # Return the base64-encoded images as a JSON response
            return json.dumps(images, indent=2)

        except Exception as e:
            # Return the error in case of failure
            return json.dumps({"error": str(e)})
