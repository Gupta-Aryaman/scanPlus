import boto3

def detectText(local_file):
   textract = boto3.client('textract', region_name='ap-south-1', aws_access_key_id = 'AKIATX3OR7WFCNAUMMNN', aws_secret_access_key= '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')

   with open(local_file,'rb') as document:
     response = textract.detect_document_text(Document={'Bytes': document.read()})
   text = ""
   for item in response["Blocks"]:
     if item["BlockType"] == "LINE":
       text = text + " " + item["Text"]
   return text