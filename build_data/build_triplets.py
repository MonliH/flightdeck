import random
import json
from tqdm import tqdm
import numpy as np
from functools import lru_cache
from typing import List, Dict, Tuple
from similar_to_others import get_similar
from datasets import Dataset, DatasetDict


id_to_doc = json.load(open("output/project_id_to_data.json", "r"))

@lru_cache(maxsize=100000)
def cached_get_similar(text: str, award_filter: str) -> List[Tuple]:
    """
    Cached wrapper for get_similar function.
    
    Args:
        text: Project description text
        award_filter: Award status to filter by ("big", "small", or "none")
        
    Returns:
        List of (project, score) tuples from get_similar
    """
    return get_similar(text, k=10, filt={"award": award_filter})

def create_triplet_dataset(
    projects: List[Dict],
    num_train: int = 15000,
    num_val: int = 500,
    num_test: int = 500,
    random_seed: int = 42,
) -> DatasetDict:
    """
    Create train/val/test triplet datasets for project success prediction.

    Args:
        projects: List of project dictionaries with 'win_status' and 'text' keys
        get_similar: Function to get semantically similar projects
        num_train: Number of training triplets
        num_val: Number of validation triplets
        num_test: Number of test triplets
        random_seed: Random seed for reproducibility

    Returns:
        DatasetDict containing train, validation, and test datasets
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Organize projects by win status
    winning_projects = [p for p in projects if p["award"] == "big"]
    partial_projects = [p for p in projects if p["award"] == "small"]
    losing_projects = [p for p in projects if p["award"] == "none"]

    def generate_triplets(
        num_samples: int, similar_ratio: float = 0.7
    ) -> Dict[str, List[str]]:
        """
        Generate triplets using both similar and random samples for positive pairs,
        ensuring no duplicates between anchor and positive samples.

        Args:
            num_samples: Number of triplets to generate
            winning_projects: List of winning project dictionaries
            partial_projects: List of partially successful project dictionaries
            losing_projects: List of unsuccessful project dictionaries
            get_similar: Function to get semantically similar projects
            similar_ratio: Ratio of similar vs random samples for positive pairs (default: 0.7)

        Returns:
            Dictionary with anchors, positives, negatives, and anchor status
        """
        anchors = []
        positives = []
        negatives = []
        anchor_status = []

        def filter_anchor_from_similar(similar_projects, anchor_text):
            """Filter out the anchor project from similar projects list."""
            return [
                id_to_doc[p.metadata["id"]]
                for p, _score in similar_projects
                if id_to_doc[p.metadata["id"]]["parsed_content"]["description_markdown"] != anchor_text
            ]

        for _ in tqdm(range(num_samples), total=num_samples):
            # Select category with focus on winning/losing
            category = random.choices(
                ["winning", "partial", "losing"], weights=[0.34, 0.33, 0.33]
            )[0]

            if category == "winning":
                anchor = random.choice(winning_projects)
                # Decide between similar or random positive
                if random.random() < similar_ratio:
                    # Get similar winning projects and filter out anchor
                    similar_winning = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": "big"},
                    )  # Get more samples to ensure we have enough after filtering
                    filtered_similar = filter_anchor_from_similar(
                        similar_winning,
                        anchor["parsed_content"]["description_markdown"],
                    )
                    if (
                        filtered_similar
                    ):  # If we have valid similar projects after filtering
                        positive = random.choice(filtered_similar)
                    else:  # Fallback to random if no valid similar projects
                        positive = random.choice(
                            [p for p in winning_projects if p != anchor]
                        )
                else:
                    # Get random winning project as positive
                    positive = random.choice(
                        [p for p in winning_projects if p != anchor]
                    )

                negative_to_sample_from = losing_projects if random.random() < 0.5 else partial_projects
                name_to_sample_from = "small" if random.random() < 0.5 else "none"
                if random.random() < similar_ratio:
                    similar_losing = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": name_to_sample_from},
                    )  # Get more samples to ensure we have enough after filtering
                    filtered_similar = filter_anchor_from_similar(
                        similar_losing,
                        anchor["parsed_content"]["description_markdown"],
                    )
                    if (
                        filtered_similar
                    ):  # If we have valid similar projects after filtering
                        negative = random.choice(filtered_similar)
                    else:  # Fallback to random if no valid similar projects
                        negative = random.choice(
                            [p for p in negative_to_sample_from if p != anchor]
                        )
                else:
                    negative = random.choice(negative_to_sample_from)

            elif category == "losing":
                anchor = random.choice(losing_projects)
                if random.random() < similar_ratio:
                    # Get similar losing projects and filter out anchor
                    similar_losing = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": "none"},
                    )
                    filtered_similar = filter_anchor_from_similar(
                        similar_losing, anchor["parsed_content"]["description_markdown"]
                    )
                    if filtered_similar:
                        positive = random.choice(filtered_similar)
                    else:
                        positive = random.choice(
                            [p for p in losing_projects if p != anchor]
                        )
                else:
                    # Get random losing project as positive
                    positive = random.choice(
                        [p for p in losing_projects if p != anchor]
                    )

                negative_to_sample_from = winning_projects if random.random() < 0.5 else partial_projects
                name_to_sample_from = "big" if random.random() < 0.5 else "small"
                if random.random() < similar_ratio:
                    similar_losing = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": name_to_sample_from},
                    )  # Get more samples to ensure we have enough after filtering
                    filtered_similar = filter_anchor_from_similar(
                        similar_losing,
                        anchor["parsed_content"]["description_markdown"],
                    )
                    if (
                        filtered_similar
                    ):  # If we have valid similar projects after filtering
                        negative = random.choice(filtered_similar)
                    else:  # Fallback to random if no valid similar projects
                        negative = random.choice(
                            [p for p in negative_to_sample_from if p != anchor]
                        )
                else:
                    negative = random.choice(negative_to_sample_from)

            else:  # partial
                anchor = random.choice(partial_projects)
                if random.random() < similar_ratio:
                    # Get similar partial projects and filter out anchor
                    similar_partial = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": "small"},
                    )
                    filtered_similar = filter_anchor_from_similar(
                        similar_partial,
                        anchor["parsed_content"]["description_markdown"],
                    )
                    if filtered_similar:
                        positive = random.choice(filtered_similar)
                    else:
                        positive = random.choice(
                            [p for p in partial_projects if p != anchor]
                        )
                else:
                    # Get random partial project as positive
                    positive = random.choice(
                        [p for p in partial_projects if p != anchor]
                    )

                # Get negative sample
                negative_to_sample_from = winning_projects if random.random() < 0.5 else losing_projects
                name_to_sample_from = "big" if random.random() < 0.5 else "none"
                if random.random() < similar_ratio:
                    similar_losing = get_similar(
                        anchor["parsed_content"]["description_markdown"],
                        k=10,
                        filt={"award": name_to_sample_from},
                    )  # Get more samples to ensure we have enough after filtering
                    filtered_similar = filter_anchor_from_similar(
                        similar_losing,
                        anchor["parsed_content"]["description_markdown"],
                    )
                    if (
                        filtered_similar
                    ):  # If we have valid similar projects after filtering
                        negative = random.choice(filtered_similar)
                    else:  # Fallback to random if no valid similar projects
                        negative = random.choice(
                            [p for p in negative_to_sample_from if p != anchor]
                        )
                else:
                    negative = random.choice(negative_to_sample_from)

            anchors.append(anchor["parsed_content"]["description_markdown"])
            positives.append(positive["parsed_content"]["description_markdown"])
            negatives.append(negative["parsed_content"]["description_markdown"])
            anchor_status.append(category)

        return {
            "anchor": anchors,
            "positive": positives,
            "negative": negatives,
            "anchor_status": anchor_status,
        }

    # Generate splits
    train_data = generate_triplets(num_train)
    val_data = generate_triplets(num_val)
    test_data = generate_triplets(num_test)

    # Create dataset dictionary
    dataset_dict = DatasetDict(
        {
            "train": Dataset.from_dict(train_data),
            "validation": Dataset.from_dict(val_data),
            "test": Dataset.from_dict(test_data),
        }
    )

    return dataset_dict


# Example usage
if __name__ == "__main__":

    projects = list(id_to_doc.values())
    dataset = create_triplet_dataset(projects)
    dataset.push_to_hub(
        "jonathanli/hackathon-triplets-large",
    )
