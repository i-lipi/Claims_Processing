import os
import io
import sys
import base64
import tempfile
import re
import streamlit as st
from PIL import Image
import boto3
import subprocess
import logging
import json
import fitz  # PyMuPDF
from together import Together
from dotenv import load_dotenv
load_dotenv()


# --- Set up the Streamlit page ---
st.set_page_config(page_title="Unified Document Processor", layout="wide")
st.title("Vision model + Crewai")



#os.environ["together_api_key"] = "Key Here"  # Replace with your actual API key
#os.environ["together_model"] = "meta-llama/Llama-Vision-Free"  # Replace with your preferred model


# os.environ["AWS_ACCESS_KEY_ID"] = "Key Here"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "Key Here"

# --- Document Source Input ---
st.header("Document Source")

uploaded_file = st.file_uploader("Upload a document (PDF, PNG, JPG, JPEG)", type=["pdf", "png", "jpg", "jpeg"])
s3_uri = st.text_input("Or enter the S3 URI for your document (e.g., s3://mybucket/myfile.pdf)")

# --- Process Document Button ---
if st.button("Process Document"):
    if not uploaded_file and not s3_uri:
        st.error("Please either upload a file or enter an S3 URI.")
    else:
        with st.spinner("Processing document..."):
            # Determine source: file upload takes precedence
            file_data = None
            file_name = ""
            from_s3 = False


            if uploaded_file:
                file_name = uploaded_file.name.lower()
                file_data = uploaded_file.getvalue()
            else:
                # Parse the S3 URI to download the file
                s3_match = re.match(r's3://([^/]+)/(.+)', s3_uri)
                if not s3_match:
                    st.error("Invalid S3 URI format. Use s3://bucket/key")
                    st.stop()
                bucket = s3_match.group(1)
                key = s3_match.group(2)
                try:
                    s3_client = boto3.client("s3")
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    file_data = response["Body"].read()
                    file_name = key.lower()
                    from_s3 = True
                except Exception as e:
                    st.error(f"Error downloading file from S3: {e}")
                    st.stop()


            # Debugging: Log file type and size
            st.write(f"File type: {file_name}")
            st.write(f"File size: {len(file_data)} bytes")
            
            # Auto-detect document type based on file extension
            images = []
            if file_name.endswith(".pdf"):
                st.info("PDF detected: Converting to images and processing via Vision model")
                # Save to temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                    temp.write(file_data)
                    temp.flush()
                    file_path = temp.name
                # Convert PDF to images using PyMuPDF
                try:
                    doc = fitz.open(file_path)
                    for page_num in range(doc.page_count):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_bytes))
                        images.append(img)
                except Exception as e:
                    st.error(f"Error converting PDF to images: {e}")
                    st.stop()


            elif file_name.endswith((".jpg", ".png", ".jpeg")):
                st.info("Image detected: Processing directly with Vision model")
                try:
                    image = Image.open(io.BytesIO(file_data))
                    image = image.convert("RGB")
                    images = [image]  # Treat image as single-page document
                except Exception as e:
                    st.error(f"Error opening image: {e}")
                    st.stop()


            # --- Display the Images Side by Side ---
            if images:
                st.success("Document processed successfully!")
                st.write(f"Document has {len(images)} pages!")
                num_columns = len(images)
                columns = st.columns(min(3, num_columns))  # Create up to 3 columns
                for page_num, img in enumerate(images):
                    # Resize image to fit within a specific width (e.g., 600px) while maintaining aspect ratio
                    max_width = 600  # Max width for the image
                    width_percent = max_width / float(img.size[0])
                    height = int((float(img.size[1]) * float(width_percent)))
                    img_resized = img.resize((max_width, height), Image.Resampling.LANCZOS)


                    # Display the resized image in the appropriate column
                    columns[page_num % 3].image(img_resized, caption=f"Page {page_num + 1}", use_column_width=True)


                # Convert the image(s) to base64 and process with the Vision model
                try:
                    # Convert images to base64 for sending to Together AI Vision model
                    base64_images = []
                    for img in images:
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG")
                        img_bytes = buffer.getvalue()
                        encoded_img = base64.b64encode(img_bytes).decode("utf-8")
                        base64_images.append(f"data:image/jpeg;base64,{encoded_img}")


                    # Process each image with Together AI Vision model
                    client = Together(api_key=together_api_key)
                    extracted_text = ""

                    

                    prompt=( "Extract and summarize all the relevant data from the document."
                    "Ensure extraction of the data the checkboxes, buttons, filled form functions, key value pairs, tabular information and other relevant information with reference or title."
                    "Specifically get the information regarding individual charges, combined charges, amount, dates, cpt, hcps, icd codes, patient information, insured information, service provider information,"
                     "service information, Physician's details, billing information and others."
                     "Return the whole exctracted text in a well defined JSON structure"
                     )
                    
                    for img_url in base64_images:
                        response = client.chat.completions.create(
                            model=together_model,
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt },
                                    {"type": "image_url", "image_url": {"url": img_url}},
                                ],
                            }]
                        )
                        extracted_text += response.choices[0].message.content


                    # Store extracted text in session state
                    st.session_state.extracted_text = extracted_text
                    st.write("Extracted Text from Document:")
                    st.text_area("Extracted Text", value=extracted_text, height=500)


                except Exception as e:
                    st.error(f"Error from Together AI Vision API: {e}")
                    
        st.success("Processing complete!")

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[
    logging.StreamHandler(sys.stdout),  # This sends logs to Streamlit's output
])       

def clean_output(output):
    # Remove ANSI escape sequences (color codes) and extra spaces/newlines
    output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z0-9]*', '', output)  # Catch all escape sequences
    # Add space between numbers and words if they are concatenated
    output = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', output)
    output = re.sub(r'[^\x00-\x7F]+', '', output)  # Remove non-ASCII characters
    output = re.sub(r'\n+', '\n', output)  # Replace multiple newlines with one
    # Remove unwanted 'self.' from the text
    output = output.replace('self.', '')
    return output.strip()  # Remove leading and trailing whitespace

# Define paths for the review and output files
review_file_path = r"D:\anaconda\visionproj\review.md"
output_file_path = r"D:\anaconda\visionproj\output.md"
final_file_path= r"D:\anaconda\visionproj\final.md"

# Function to read the content of the file
def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        return "File not found."
    
def process_with_crewai(extracted_text):
    # Prepare the data to be passed to CrewAI (only the extracted text)
    inputs = {
        'extracted_text': extracted_text
    }

    # Pass inputs to CrewAI via subprocess
    crewai_path = r"D:\anaconda\visionproj\src\visionproj\main.py"  # Use absolute path to main.py

    try:
        logging.debug(f"Inputs being sent to CrewAI: {json.dumps(inputs)}")
        
        process = subprocess.Popen(
            ["python", crewai_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            
        )
        stdout, stderr = process.communicate(input=json.dumps(inputs))  # Send data and get output
        
        clean_stdout = clean_output(stdout)
        logging.info(f"CrewAI stdout (cleaned): {clean_stdout}")
        logging.info(f"CrewAI stdout: {stdout}")
        logging.info(f"CrewAI stderr: {stderr}")
        
        
        if process.returncode == 0:
            st.success("CrewAI processing completed.")
            
            # Read and display both review and output agent results
            review_content = read_file(review_file_path)
            output_content = read_file(output_file_path)
            final_content= read_file(final_file_path)
            
            st.subheader("Review Agent Output")
            st.text_area("Review Output", value=review_content, height=400)
            
            st.subheader("Claim Decision Maker Output")
            st.markdown(f"**{output_content}**")
            
            st.subheader("Final decision")
            st.markdown(f"**{final_content}**")
            
            # Optionally, display the full CrewAI log or processing output
            st.subheader("CrewAI Processing logs")
            st.text_area("Processing Logs", value=stdout, height=600)
            
            
        else:
            st.error("Error processing with CrewAI.")
            st.write("Error output from CrewAI:", stderr.strip())  # Display error (stderr)

    except Exception as e:
        st.error(f"Error with subprocess: {e}")


# Button to trigger CrewAI processing
if st.button("Process with CrewAI"):
    if "extracted_text" in st.session_state:
        # Call CrewAI program to process the extracted text
        st.success("Triggering CrewAI processing...")
        
        # Here, you would call the CrewAI processing function
        process_with_crewai(st.session_state.extracted_text)
    else:
        st.error("No extracted text available.") 
