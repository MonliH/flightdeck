from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

import dotenv

import os

dotenv.load_dotenv()

api_key = os.getenv("COHERE_API_KEY")
api_key_prod = os.getenv("COHERE_API_KEY_PROD")

embeddings = CohereEmbeddings(
    cohere_api_key=api_key,
    base_url="https://stg.api.cohere.com/",
    model="embed-english-v3.0",
)

persist_dir = "./chroma_langchain_db"
print("loading db")
db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
print("done loading db")

def get_similar(doc, k, filt=None):
    results = db.similarity_search_with_score(doc, k=k, filter=filt)
    return results
