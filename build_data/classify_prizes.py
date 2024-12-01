import cohere
from tqdm import tqdm
import json
import dotenv
import os
from multiprocessing import Pool, cpu_count
from functools import partial

def load_awards():
    awards = set()
    with open("output/projects_parsed_deduped.jsonl", "r") as file:
        for line in file:
            data = json.loads(line)
            for sub in data["parsed_content"]["submissions"]:
                awards.update(sub["awards"])
    return list(awards)

def process_award(award, api_key, base_url):
    # Create a new client for each process to avoid sharing connections
    co = cohere.Client(
        api_key=api_key,
        base_url=base_url,
    )
    
    res = co.chat(
        model="command-r-plus-08-2024",
        message=award,
        temperature=0,
        chat_history=[
            {"role": "system", "message": """You are tasked with classifying a list of hackathon prizes into two categories: Big Wins and Small Wins.

Criteria for Classifying the Prizes:

Overall Winners or Finalists: Big Wins are typically awarded to projects that are recognized as overall winners or finalists in the hackathon. These are the top prizes, often with significant financial rewards, prestige, and media visibility. Big wins should explicitly be a finalist of the hackathon. Small Wins are usually given for specific technical achievements or contributions in particular areas (e.g., best use of a certain tool or API). These prizes may be valuable but are often narrower in scope and impact compared to overall wins.

Big wins should NOT be for a specific challenge. Big wins should not include ANY MLH prizes or ANY non-podium or non-placement prize. For example, any "challenge" prizes should be included as a small prize.

Example of big wins: Overall 1st place, 2nd place, or 3rd. Overall finalist. Any specified place should be considered a big win (e.g. 4th place, 5th place, etc.)
Example of small wins: Any MLH prize, any prize specifically for using a technology.

Instructions: Classify each prompt inputted as either a "Big Win" or "Small Win" based on the criteria provided, with a priority given to overall winners or finalists as large prizes."""}
        ],
        prompt_truncation="AUTO",
        connectors=[],
    )
    
    return award, "Big Win" if "big win" in res.text.lower() else "Small Win"

def main():
    # Load environment variables
    dotenv.load_dotenv()
    api_key = os.getenv("COHERE_API_KEY")
    base_url = "https://stg.api.cohere.com/"
    
    # Load awards
    awards = load_awards()
    
    # Determine optimal number of processes (use 75% of available CPU cores)
    num_processes = 50
    
    # Create partial function with fixed arguments
    process_award_partial = partial(process_award, api_key=api_key, base_url=base_url)
    
    # Create process pool and map awards to processes
    with Pool(num_processes) as pool:
        # Use tqdm to show progress
        results = list(tqdm(
            pool.imap(process_award_partial, awards),
            total=len(awards),
            desc="Processing awards"
        ))
    
    # Convert results to dictionary
    awards_mapping = dict(results)
    
    # Save results
    with open("output/awards_mapping.json", "w") as f:
        json.dump(awards_mapping, f)

if __name__ == "__main__":
    main()
