import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_text(local_file, region_name, aws_access_key_id, aws_secret_access_key):
    """
    Detects text from a local file using Amazon Textract.
    
    :param local_file: Path to the local file to be analyzed.
    :param region_name: AWS region name for Textract.
    :param aws_access_key_id: AWS access key ID.
    :param aws_secret_access_key: AWS secret access key.
    :return: Extracted text or error message.
    """
    try:
        # Initialize Textract client
        textract = boto3.client(
            'textract', 
            region_name=region_name, 
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key
        )

        # Open file and detect text
        with open(local_file, 'rb') as document:
            response = textract.detect_document_text(Document={'Bytes': document.read()})

        # Extract text from response
        text_lines = [
            item["Text"]
            for item in response.get("Blocks", [])
            if item.get("BlockType") == "LINE"
        ]
        extracted_text = " ".join(text_lines)
        logger.info(f"Successfully extracted text from {local_file}")

        return extracted_text

    except (BotoCoreError, ClientError) as e:
        logger.error(f"Failed to process file {local_file}: {e}")
        return f"Error: {e}"

    except FileNotFoundError:
        logger.error(f"File {local_file} not found.")
        return "Error: File not found."

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return f"Error: {e}"
