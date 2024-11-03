# Handwritten Doctor's Prescription to Text Conversion, Classification System and Medicine Scheduler

## Project Description:
The goal of this project is to develop a system that can convert doctor's handwritten prescriptions into machine-readable text and classify the medicines along with their doses. The system will also send an alert to the patient's registered email address containing all the relevant prescription details. The project utilizes Natural Language Processing (NLP).

Key features:
* AWS Textract: Extracts text from doctor's handwritten prescriptions.
* NER Model: Classifies the extracted text into relevant categories.
* Alert System: Sends an email alert containing all the prescription details (medicines, doses, and category) to the patient's registered email address.

## OCR and NER Pipeline for Prescription Processing

1. **OCR (Optical Character Recognition)**  
   - Converts handwritten doctor prescriptions into machine-readable text using OCR techniques.

2. **NER (Named Entity Recognition)**  
   - **Input:** Text from the OCR step containing unstructured data such as medicine names and dosage instructions.
   - **BERT Embedding:** Converts the input text into context-aware embeddings.
   - **CHAR CNN-BiLSTM:**  
     - Character-level CNN captures morphological features of words.
     - BiLSTM captures bidirectional context of the text sequence.
   - **CRF (Conditional Random Field):** Ensures valid label sequences for structured output like medicine names, dosages, and eating schedules.

**Output:** Structured data with medicine names, dosages, and schedules extracted from the text.

## Technologies Used:
- Python
- Natural Language Processing (NLP) techniques
- AWS Textract 
- Named Entity Recognition (NER) techniques
- Machine Learning Algorithms
- Cron Jobs

## Setup Instructions
To set up the project locally, follow these steps:
1. Clone the repository
```
git clone https://github.com/Gupta-Aryaman/scanPlus.git
cd scanPlus
```
2. Create a virtual environment
```
python3 -m venv venv
source venv/bin/activate   # On Windows use `venv\Scripts\activate`
```
3. Install the required dependencies
```
pip install -r requirements.txt
```
4. Configure AWS Textract
   - Ensure you have AWS credentials configured. You can use the AWS CLI to set this up:
  ```
  aws configure
  ```
6. Run the project
```
python main.py
```
7. Set up Cron Jobs (if applicable)
   - Configure the cron jobs as per your requirements to automate tasks.

## Usage
1. Upload or provide the handwritten prescription image to the system.
2. The system will process the image, extract text, classify it, and send an email with the prescription details.

## Contributing
1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature-branch).
5. Open a pull request.

## License
This project is licensed under the [MIT License](https://github.com/Gupta-Aryaman/scanPlus/blob/main/LICENSE).
