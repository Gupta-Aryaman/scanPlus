import sparknlp
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from sparknlp.annotator import *
from sparknlp.training import CoNLL
from sparknlp.base import DocumentAssembler
import logging
from pyspark.sql import functions as F

from ml_model import detect_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InitiateNER:
    def __init__(self, gpu=True, embedding_model='bert_base_uncased', language='en'):
        # Initialize Spark session
        self.spark = sparknlp.start(gpu=gpu)
        logger.info("Spark NLP session started.")

        # Initialize embeddings and NER tagger
        self.bert_embeddings = BertEmbeddings.pretrained(embedding_model, language) \
            .setInputCols(["sentence", 'token']) \
            .setOutputCol("embeddings") \
            .setCaseSensitive(False)

        self.ner_tagger = NerDLApproach() \
            .setInputCols(["sentence", "token", "embeddings"]) \
            .setLabelColumn("label") \
            .setOutputCol("ner") \
            .setMaxEpochs(20) \
            .setLr(0.001) \
            .setPo(0.005) \
            .setBatchSize(32) \
            .setValidationSplit(0.1) \
            .setUseBestModel(True) \
            .setEnableOutputLogs(True)
        
        # Initialize other components for prediction
        self.document_assembler = DocumentAssembler() \
            .setInputCol("text") \
            .setOutputCol("document")

        self.sentence_detector = SentenceDetector() \
            .setInputCols(['document']) \
            .setOutputCol('sentence')

        self.tokenizer = Tokenizer() \
            .setInputCols(['sentence']) \
            .setOutputCol('token')

        self.converter = NerConverter() \
            .setInputCols(["document", "token", "ner"]) \
            .setOutputCol("ner_span")

    def train_model(self, training_file, save_path):
        try:
            training_data = CoNLL().readDataset(self.spark, training_file)
            training_data = self.bert_embeddings.transform(training_data).drop("text", "document", "pos")

            logger.info("Training model...")
            self.ner_model = self.ner_tagger.fit(training_data)
            logger.info("Model trained successfully.")

            self.ner_model.write().overwrite().save(save_path)
            logger.info(f"Model saved at: {save_path}")

        except Exception as e:
            logger.error(f"Error during training: {e}")

    def load_model(self, model_path):
        try:
            self.loaded_ner_model = NerDLModel.load(model_path) \
                .setInputCols(["sentence", "token", "embeddings"]) \
                .setOutputCol("ner")

            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")

    def predict(self, text):
        try:
            # Create or reuse prediction pipeline
            if not hasattr(self, 'prediction_pipeline'):
                self.prediction_pipeline = Pipeline(
                    stages=[
                        self.document_assembler,
                        self.sentence_detector,
                        self.tokenizer,
                        self.bert_embeddings,
                        self.loaded_ner_model,
                        self.converter
                    ]
                )
                logger.info("Prediction pipeline created.")

            sample_data = self.spark.createDataFrame([[text]]).toDF("text")
            prediction_model = self.prediction_pipeline.fit(self.spark.createDataFrame([['']]).toDF("text"))
            preds = prediction_model.transform(sample_data)
            pipeline_result = preds.collect()[0]

            return self.format_output(pipeline_result)

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return {"error": str(e)}

    @staticmethod
    def format_output(pipeline_result):
        result_dict = {}
        for entity in pipeline_result.ner_span:
            entity_type = entity.metadata['entity']
            result_dict.setdefault(entity_type, []).append(
                (entity.result, (entity.begin, entity.end))
            )
        return result_dict
    
ner_model = InitiateNER()
# ner_model.train_model("../content/NERDataset.txt", "../content/model")

ner_model.load_model("../content/model")
print(ner_model.predict(detect_text("../images/prescriptions/check2.jpeg")))