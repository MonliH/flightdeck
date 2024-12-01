from fastapi import FastAPI, Body
from typing import Optional
from pydantic import BaseModel
import similar_to_others
from scrape.devpost_page_scraper import DevpostScraper
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uid_to_project = json.load(open("output/project_id_to_data.json", "r"))

def is_valid_url(url_string):
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])  # Check if both scheme and network location exist
    except:
        return False

class RequestParams(BaseModel):
    document_or_link: str
    k: int
    filter: Optional[str] = None

@app.post("/similar")
def get_similar(request_params: RequestParams=Body(default=None)):
    document_or_link = request_params.document_or_link
    k = request_params.k
    filter = request_params.filter

    document = document_or_link
    if is_valid_url(document_or_link):
        document = DevpostScraper().scrape_submission(document_or_link)["description_markdown"]
    similar = similar_to_others.get_similar(document, k, filter)

    data = []
    for res, score in similar:
        project = uid_to_project[res.metadata["id"]]
        data.append((score, project))
    
    data.sort(key=lambda x: x[0], reverse=True)

    return data
