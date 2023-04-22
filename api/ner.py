import sparknlp
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline

import sparknlp
from sparknlp.annotator import *
from sparknlp.common import *
from sparknlp.training import CoNLL
from sparknlp.base import *
# from sparknlp_display import NerVisualizer
# import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
from pyspark.sql.functions import *
import pickle
# from sklearn.metrics import accuracy_score, classification_report
import itertools
import math
import csv
from ml_model import *

spark = sparknlp.start(gpu=True)


class initiate_ner(object):
    def __init__(self):
        self.bert_embeddings = BertEmbeddings.pretrained('bert_base_uncased', 'en') \
            .setInputCols(["sentence", 'token']) \
            .setOutputCol("embeddings") \
            .setMaxSentenceLength(512) \
            .setCaseSensitive(False)
        self.nerTagger = NerDLApproach() \
            .setInputCols(["sentence", "token", "embeddings"]) \
            .setLabelColumn("label") \
            .setOutputCol("ner") \
            .setMaxEpochs(20) \
            .setLr(0.001) \
            .setPo(0.005) \
            .setBatchSize(32) \
            .setRandomSeed(44) \
            .setVerbose(2) \
            .setValidationSplit(0.1) \
            .setUseBestModel(True) \
            .setEvaluationLogExtended(True) \
            .setEnableOutputLogs(True)

    def train_model(self, training_file, save_path):
        # train the model and save it in the model folder.
        training_data = CoNLL().readDataset(spark, training_file)

        training_data = self.bert_embeddings.transform(training_data)

        training_data = training_data.drop("text", "document", "pos")

        # nerTagger = NerDLApproach() \
        #     .setInputCols(["sentence", "token", "embeddings"]) \
        #     .setLabelColumn("label") \
        #     .setOutputCol("ner") \
        #     .setMaxEpochs(20) \
        #     .setLr(0.001) \
        #     .setPo(0.005) \
        #     .setBatchSize(32) \
        #     .setRandomSeed(44) \
        #     .setVerbose(2) \
        #     .setValidationSplit(0.1) \
        #     .setUseBestModel(True) \
        #     .setEvaluationLogExtended(True) \
        #     .setEnableOutputLogs(True)

        print("[Training...]")
        self.ner_model = self.nerTagger.fit(training_data)
        print("[Model trained!]")

        self.ner_model.write().overwrite().save(save_path)
        print(f"[Model saved to the path: {save_path}]")

    def load_model(self, save_path="/content/model_path"):
        self.loaded_ner_model = NerDLModel.load(save_path) \
            .setInputCols(["sentence", "token", "embeddings"]) \
            .setOutputCol("ner")

        print("[Model loaded!]")

    def predict(self, text):
        # load the model and get a dict containing predictions alongwith the accuracy.
        document = DocumentAssembler() \
            .setInputCol("text") \
            .setOutputCol("document")

        sentence = SentenceDetector() \
            .setInputCols(['document']) \
            .setOutputCol('sentence')

        token = Tokenizer() \
            .setInputCols(['sentence']) \
            .setOutputCol('token')

        # Convert (B-PER I-PER) => (PER)
        converter = NerConverter() \
            .setInputCols(["document", "token", "ner"]) \
            .setOutputCol("ner_span")

        ner_prediction_pipeline = Pipeline(
            stages=[
                document,
                sentence,
                token,
                self.bert_embeddings,
                self.loaded_ner_model,
                converter])
        empty_data = spark.createDataFrame([['']]).toDF("text")
        prediction_model = ner_prediction_pipeline.fit(empty_data)

        sample_data = spark.createDataFrame([[text]]).toDF("text")
        preds = prediction_model.transform(sample_data)

        pipeline_result = preds.collect()[0]

        def make_dict(pipeline_result=pipeline_result):
            dic = {}

            for word in pipeline_result.asDict()['ner_span']:
                if word.asDict()['metadata']['entity'] != 'O':
                    if word.asDict()['metadata']['entity'] not in dic.keys():
                        dic[word.asDict()['metadata']['entity']] = [
                            (word.asDict()['result'], (word.asDict()['begin'], word.asDict()['end']))]
                    else:
                        dic[word.asDict()['metadata']['entity']].append(
                            (word.asDict()['result'], (word.asDict()['begin'], word.asDict()['end'])))

            return dic

        return make_dict()
    
# ner_model = initiate_ner()



# ner_model.load_model("/home/aryaman/Desktop/raj-it/content/model")
# print(ner_model.predict(detectText("./images/prescriptions/check2.jpeg")))