from langchain.retrievers import ContextualCompressionRetriever
import uuid
import json
from langchain_cohere import CohereEmbeddings
from langchain_cohere import ChatCohere
from langchain_cohere import CohereRerank, CohereRagRetriever
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader

import dotenv

from langchain_core.documents import Document

import os

dotenv.load_dotenv()

api_key = os.getenv("COHERE_API_KEY")

embeddings = CohereEmbeddings(cohere_api_key=api_key,
                                base_url="https://stg.api.cohere.com/",
                              model="embed-english-v3.0")

# Load text files and split into chunks, you can also use data gathered elsewhere in your application
documents = []
project_id_to_data = {}
award_mapping = json.load(open("output/awards_mapping.json", "r"))
with open("output/projects_parsed_final.jsonl", "r") as file:
    for line in file:
        data = json.loads(line)
        id_data = str(uuid.uuid4())
        awards = []
        for sub in data["parsed_content"]["submissions"]:
            for award in sub["awards"]:
                awards.append(award_mapping[award])
        
        award = "none"
        if "Big Win" in awards:
            award = "big"
        elif "Small Win" in awards:
            award = "small"
        
        data["award"] = award

        documents.append(Document(
            data["parsed_content"]["description_markdown"],
            metadata={"id": id_data, "award": award}
        ))
        
        project_id_to_data[id_data] = data

json.dump(project_id_to_data, open("output/project_id_to_data.json", "w"))
db = Chroma.from_documents(
    documents,
    embeddings,
    persist_directory="./chroma_langchain_db"
)
