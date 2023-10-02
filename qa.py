from haystack.document_stores import InMemoryDocumentStore
from haystack.utils import fetch_archive_from_http
import os 
from haystack.pipelines.standard_pipelines import TextIndexingPipeline
from haystack.nodes import BM25Retriever
from haystack.nodes import FARMReader
from haystack.pipelines import ExtractiveQAPipeline
from pprint import pprint
from haystack.utils import print_answers

document_store = InMemoryDocumentStore(use_bm25=True)
retriever = BM25Retriever(document_store=document_store)
reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)
pipe = ExtractiveQAPipeline(reader, retriever)



doc_dir = "d:\\data\\"
'''
fetch_archive_from_http(
    url="https://s3.eu-central-1.amazonaws.com/deepset.ai-farm-qa/datasets/documents/wiki_gameofthrones_txt1.zip",
    output_dir=doc_dir,
)
'''


files_to_index = [doc_dir + "/" + f for f in os.listdir(doc_dir)]
print('file to index ', files_to_index)
indexing_pipeline = TextIndexingPipeline(document_store)
indexing_pipeline.run_batch(file_paths=files_to_index)

prediction = pipe.run(
    query="which company does Chandrabhan work for ?", params={"Retriever": {"top_k": 10}, "Reader": {"top_k": 5}}
)

#pprint(prediction)

print_answers(prediction, details="minimum")  ## Choose from `minimum`, `medium`, and `all`
print('11111111    -----------------------------------')
print_answers(prediction, details="medium") 
 ## Choose from `minimum`, `medium`, and `all`
print('2222222222 -----------------------------------')
print_answers(prediction, details="all") 
