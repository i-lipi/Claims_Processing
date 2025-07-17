This project implements an AI-driven claims processing system using the CrewAI multi-agent framework, integrated with LangChain's Textract module and Vision LLMs to analyze healthcare and insurance-related documents.

The pipeline processes PDFs, images, and scanned receipts to extract structured data, classify the claim type, and make rule-based decisions—enhancing automation, accuracy, and scalability in real-world document workflows reducing the manual time and effort by 85%.

Document Ingestion & OCR
- Supports uploads from local paths or S3.
- OCR is performed using:
    * LangChain-integrated AWS Textract – for robust key-value, table, and form extraction.
    * Vision LLMs (e.g., Together.ai/OpenAI) – for reading receipts, images, and unstructured or handwritten text.

CrewAI Agent Workflow
- Defined via agents.yaml and tasks.yaml.

Workflow:

Review Agent: Parses and classifies the document type (e.g., dental, vision, compensation, mental health), and extracts relevant fields like patient info, service date, etc.

Claim Decision Agent: Applies deterministic business rules from a configured knowledge_sources file to classify the claim as Accepted, Rejected, or Queued, along with a confidence score (1–100).

Final Decision Validator: Verifies the decision. If confidence < 90, overrides to Queued for manual review.

🗃️ Data Persistence

Final output (claim summary, classification, decision, confidence score, and client metadata) is stored in a PostgreSQL database as JSON objects for  querying 
