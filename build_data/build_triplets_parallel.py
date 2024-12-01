import random
import json
from tqdm import tqdm
import numpy as np
from functools import lru_cache
from typing import List, Dict, Tuple
from similar_to_others import get_similar
from datasets import Dataset, DatasetDict
import multiprocessing as mp

id_to_doc = json.load(open("output/project_id_to_data.json", "r"))

@lru_cache(maxsize=100000)
def cached_get_similar(text: str, award_filter: str) -> List[Tuple]:
    """
    Cached wrapper for get_similar function.
    """
    return get_similar(text, k=10, filt={"award": award_filter})

def generate_single_triplet(args):
    """
    Generate a single triplet. This function will be called by each process.
    
    Args:
        args: Tuple containing (similar_ratio, winning_projects, partial_projects, losing_projects)
        
    Returns:
        Dictionary containing single triplet data
    """
    similar_ratio, winning_projects, partial_projects, losing_projects = args
    
    # Select category with focus on winning/losing
    category = random.choices(
        ["winning", "partial", "losing"], weights=[0.34, 0.33, 0.33]
    )[0]
    
    if category == "winning":
        anchor = random.choice(winning_projects)
        # Decide between similar or random positive
        if random.random() < similar_ratio:
            similar_winning = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                "big",
            )
            filtered_similar = filter_anchor_from_similar(
                similar_winning,
                anchor["parsed_content"]["description_markdown"],
            )
            if filtered_similar:
                positive = random.choice(filtered_similar)
            else:
                positive = random.choice([p for p in winning_projects if p != anchor])
        else:
            positive = random.choice([p for p in winning_projects if p != anchor])

        negative_to_sample_from = losing_projects if random.random() < 0.5 else partial_projects
        name_to_sample_from = "small" if random.random() < 0.5 else "none"
        if random.random() < similar_ratio:
            similar_losing = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                name_to_sample_from,
            )
            filtered_similar = filter_anchor_from_similar(
                similar_losing,
                anchor["parsed_content"]["description_markdown"],
            )
            negative = random.choice(filtered_similar) if filtered_similar else random.choice(
                [p for p in negative_to_sample_from if p != anchor]
            )
        else:
            negative = random.choice(negative_to_sample_from)

    elif category == "losing":
        anchor = random.choice(losing_projects)
        if random.random() < similar_ratio:
            similar_losing = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                "none",
            )
            filtered_similar = filter_anchor_from_similar(
                similar_losing,
                anchor["parsed_content"]["description_markdown"],
            )
            positive = random.choice(filtered_similar) if filtered_similar else random.choice(
                [p for p in losing_projects if p != anchor]
            )
        else:
            positive = random.choice([p for p in losing_projects if p != anchor])

        negative_to_sample_from = winning_projects if random.random() < 0.5 else partial_projects
        name_to_sample_from = "big" if random.random() < 0.5 else "small"
        if random.random() < similar_ratio:
            similar_winning = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                name_to_sample_from,
            )
            filtered_similar = filter_anchor_from_similar(
                similar_winning,
                anchor["parsed_content"]["description_markdown"],
            )
            negative = random.choice(filtered_similar) if filtered_similar else random.choice(
                [p for p in negative_to_sample_from if p != anchor]
            )
        else:
            negative = random.choice(negative_to_sample_from)

    else:  # partial
        anchor = random.choice(partial_projects)
        if random.random() < similar_ratio:
            similar_partial = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                "small",
            )
            filtered_similar = filter_anchor_from_similar(
                similar_partial,
                anchor["parsed_content"]["description_markdown"],
            )
            positive = random.choice(filtered_similar) if filtered_similar else random.choice(
                [p for p in partial_projects if p != anchor]
            )
        else:
            positive = random.choice([p for p in partial_projects if p != anchor])

        negative_to_sample_from = winning_projects if random.random() < 0.5 else losing_projects
        name_to_sample_from = "big" if random.random() < 0.5 else "none"
        if random.random() < similar_ratio:
            similar_other = cached_get_similar(
                anchor["parsed_content"]["description_markdown"],
                name_to_sample_from,
            )
            filtered_similar = filter_anchor_from_similar(
                similar_other,
                anchor["parsed_content"]["description_markdown"],
            )
            negative = random.choice(filtered_similar) if filtered_similar else random.choice(
                [p for p in negative_to_sample_from if p != anchor]
            )
        else:
            negative = random.choice(negative_to_sample_from)

    return {
        "anchor": anchor["parsed_content"]["description_markdown"],
        "positive": positive["parsed_content"]["description_markdown"],
        "negative": negative["parsed_content"]["description_markdown"],
        "anchor_status": category
    }

def filter_anchor_from_similar(similar_projects, anchor_text):
    """Filter out the anchor project from similar projects list."""
    return [
        id_to_doc[p.metadata["id"]]
        for p, _score in similar_projects
        if id_to_doc[p.metadata["id"]]["parsed_content"]["description_markdown"] != anchor_text
    ]

def generate_triplets_parallel(
    num_samples: int,
    winning_projects: List[Dict],
    partial_projects: List[Dict],
    losing_projects: List[Dict],
    similar_ratio: float = 0.7,
    num_processes: int = None
) -> Dict[str, List[str]]:
    """
    Generate triplets in parallel using multiple processes.
    """
    # Create the exact number of tasks we need
    args_list = [(similar_ratio, winning_projects, partial_projects, losing_projects) 
                 for _ in range(num_samples)]
    
    # Create pool of workers
    with mp.Pool(processes=num_processes) as pool:
        # Process triplets in parallel with progress bar
        results = list(tqdm(
            pool.imap(generate_single_triplet, args_list),
            total=num_samples,
            desc="Generating triplets"
        ))
    
    # Combine results
    combined_results = {
        "anchor": [],
        "positive": [],
        "negative": [],
        "anchor_status": []
    }
    
    for result in results:
        combined_results["anchor"].append(result["anchor"])
        combined_results["positive"].append(result["positive"])
        combined_results["negative"].append(result["negative"])
        combined_results["anchor_status"].append(result["anchor_status"])
    
    return combined_results

def create_triplet_dataset(
    projects: List[Dict],
    num_train: int = 20000,
    num_val: int = 500,
    num_test: int = 500,
    random_seed: int = 42,
    num_processes: int = 8
) -> DatasetDict:
    """
    Create train/val/test triplet datasets for project success prediction using parallel processing.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Organize projects by win status
    winning_projects = [p for p in projects if p["award"] == "big"]
    partial_projects = [p for p in projects if p["award"] == "small"]
    losing_projects = [p for p in projects if p["award"] == "none"]

    # Generate splits in parallel
    train_data = generate_triplets_parallel(
        num_train, winning_projects, partial_projects, losing_projects, num_processes=num_processes
    )
    val_data = generate_triplets_parallel(
        num_val, winning_projects, partial_projects, losing_projects, num_processes=num_processes
    )
    test_data = generate_triplets_parallel(
        num_test, winning_projects, partial_projects, losing_projects, num_processes=num_processes
    )

    # Create dataset dictionary
    dataset_dict = DatasetDict(
        {
            "train": Dataset.from_dict(train_data),
            "validation": Dataset.from_dict(val_data),
            "test": Dataset.from_dict(test_data),
        }
    )

    return dataset_dict

if __name__ == "__main__":
    projects = list(id_to_doc.values())
    dataset = create_triplet_dataset(projects)
    dataset.push_to_hub(
        "jonathanli/hackathon-triplets-large-2",
    )
