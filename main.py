from fastapi import FastAPI, Body
import httpx
from typing import Optional, List
from pydantic import BaseModel
from openai import OpenAI
import similar_to_others
from scrape.devpost_page_scraper import DevpostScraper
from urllib.parse import urlparse
from fastapi.middleware.cors import CORSMiddleware
import json

client = OpenAI()
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
        return all(
            [result.scheme, result.netloc]
        )  # Check if both scheme and network location exist
    except:
        return False


class RequestParams(BaseModel):
    document_or_link: str
    k: int
    filter: Optional[dict] = None


@app.post("/similar")
def get_similar(request_params: RequestParams = Body(default=None)):
    document_or_link = request_params.document_or_link
    k = request_params.k
    filter = request_params.filter

    document = document_or_link
    if is_valid_url(document_or_link):
        document = DevpostScraper().scrape_submission(document_or_link)[
            "description_markdown"
        ]
    similar = similar_to_others.get_similar(document, k, filter)

    data = []
    for res, score in similar:
        project = uid_to_project[res.metadata["id"]]
        data.append((score, project))

    data.sort(key=lambda x: x[0], reverse=True)

    return data


class SuggestionParams(BaseModel):
    project_doc: str


prompt = """Here's a bunch of projects that won hackathons that are similar to mine:
{winning_projects}

---

Here's my idea:
{user_project}

Help me make a writeup that uses ideas from the winning teams but keeps my idea the same. Only write the hackathon writeup. Put things in code tags that are key to winning. Keep the writeup easy and fun to read. Start with a title."""


class Suggestion(BaseModel):
    writeup: str
    summary: str


class SuggestionReturn(BaseModel):
    similar_projects: List[dict]
    sorted_suggestions: List[str]


similarity_server = "http://localhost:8001"


@app.post("/arena")
async def make_arena(
    params: SuggestionParams = Body(default=None),
) -> SuggestionReturn:
    doc = params.project_doc
    similar = similar_to_others.get_similar(doc=doc, k=5, filt={"award": "big"})

    similar_projects = [uid_to_project[res.metadata["id"]] for res, _ in similar]
    texts_that_are_similar = [s["parsed_content"]["description_markdown"] for s in similar_projects]
    similar = "\n\n---\n\n".join(
        texts_that_are_similar
    )

    p = prompt.format(winning_projects=similar, user_project=doc)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": [{"type": "text", "text": p}]},
        ],
        response_format={"type": "text"},
        temperature=1,
        max_tokens=4096,
        top_p=1,
        n=10,
        frequency_penalty=0,
        presence_penalty=0,
    )

    choices = [r.message.content for r in response.choices]

    async with httpx.AsyncClient() as c:
        # Set default headers if none provided
        headers = {"Content-Type": "application/json"}

        # Make the POST request
        response = await c.post(
            similarity_server + "/similarity",
            json={"good_projects": texts_that_are_similar, "other_projects": choices},
            headers=headers,
            timeout=30.0,
        )

        sim = response.json()

    sorted_suggestions = [x for x, _ in sorted(list(zip(choices, sim)), key=lambda x: x[1], reverse=True)]

    return SuggestionReturn(
        similar_projects=similar_projects,
        sorted_suggestions=sorted_suggestions,
    )


class WhatTheyDidParams(BaseModel):
    documents: List[str]


@app.post("/what-they-did")
async def what_they_did(docs: WhatTheyDidParams = Body(default=None)):
    d = docs.documents
    summary = []
    for doc in d:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": doc + "\n\nSummarize this hackathon project, focusing on its key features and the problem it solves. Use clear and engaging language. Keep the generated text interesting, non-generic, and sound non-AI generated. Prioritize making the functionality of the project clear in the generated text. The generated text only mention features of the project, not any external information such as which hackathon it was at, the team that made it, or the prizes it won. Bold the name of the project. The generated text should be 1 short, information dence sentence. The sentence should be no more than 10 words.",
                        }
                    ],
                },
            ],
            response_format={"type": "text"},
            temperature=1,
            max_tokens=200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        what_they_did = response.choices[0].message.content
        summary.append(what_they_did)

    return summary

class WhatTheyDidParams(BaseModel):
    documents: List[str]
    prizes: List[str]
    names: List[str]


@app.post("/how-they-won")
async def what_won(docs: WhatTheyDidParams = Body(default=None)):
    d = docs.documents
    p = docs.prizes
    n = docs.names
    summary = []
    for doc, prize, name in zip(d, p, n):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": doc + f"\n\nThe above hackathon project won: {prize}. Identify the top reason why it was the winner. Consider aspects such as innovation, technical execution, impact, usability. In particular consider why the project stood out. The reason you use should be explicitly stated within the project. The reason the project won should not just be a description of the project. Write one short sentence. The sentence should be less than 10 words. Output the generated sentence only. Bold a keyword related to why it won, and do not bold the project name. Referring to the project should be done in past tense. Start your sentence with: {name} won because",
                        }
                    ],
                },
            ],
            response_format={"type": "text"},
            temperature=1,
            max_tokens=200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        what_they_did = response.choices[0].message.content
        summary.append(what_they_did)

    return summary
