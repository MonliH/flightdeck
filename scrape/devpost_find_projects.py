import requests
from urllib.parse import urlparse

from tqdm import tqdm
from bs4 import BeautifulSoup
import time
import json
from typing import List, Dict, Optional
import pandas as pd


class DevPostScraper:
    def __init__(
        self,
        base_url: str = "https://hackthenorth2024.devpost.com/project-gallery",
        output_file="output/devpost_projects.jsonl",
    ):
        self.base_url = base_url
        self.session = requests.Session()
        # Add headers to mimic a browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.output_file = output_file

    def get_page_content(self, page: int = 1) -> Optional[BeautifulSoup]:
        """
        Fetch the content of a specific page
        """
        try:
            response = self.session.get(f"{self.base_url}?page={page}")
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return None

    def parse_project(self, project_element) -> Dict:
        """
        Extract information from a single project element
        """
        try:
            # Get basic project info
            title = project_element.find("h5").text.strip()
            tagline = project_element.find("p", class_="small tagline").text.strip()

            # Get project URL
            project_url = project_element.find_parent("a")["href"]

            # Get likes and comments count
            likes = project_element.find("span", {"data-count": "like"}).text.strip()
            comments = project_element.find(
                "span", {"data-count": "comment"}
            ).text.strip()

            # Get team members
            members_div = project_element.find("div", class_="members")
            members = []
            if members_div:
                for member in members_div.find_all("span", class_="user-profile-link"):
                    member_url = member.get("data-url", "")
                    member_name = member.img.get("alt", "")
                    members.append({"name": member_name, "profile_url": member_url})

            # Check if project is a winner
            winner_badge = project_element.find("aside", class_="entry-badge")
            is_winner = bool(winner_badge and "Winner" in winner_badge.text)

            # Get thumbnail image URL if available
            thumbnail = project_element.find("img", class_="software_thumbnail_image")
            thumbnail_url = thumbnail.get("src") if thumbnail else None

            return {
                "title": title,
                "tagline": tagline,
                "project_url": project_url,
                "thumbnail_url": thumbnail_url,
                "likes": int("".join(filter(str.isdigit, likes))),
                "comments": int("".join(filter(str.isdigit, comments))),
                "team_members": members,
                "is_winner": is_winner,
            }
        except Exception as e:
            print(f"Error parsing project: {e}")
            return {}

    def get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        Extract the total number of pages from the pagination info
        """
        try:
            # Find the items info text that shows total number of items
            items_info = soup.find("span", class_="items_info")
            if items_info:
                text = items_info.text
                # Extract total number from text like "1 – 24 of 235"
                total_items = int(text.split("of")[-1].strip())
                # Calculate total pages (24 items per page)
                return (total_items + 23) // 24  # Ceiling division by 24
            return 1
        except Exception as e:
            print(f"Error getting total pages: {e}")
            return 1

    def scrape_projects(self, start_page: int = 1) -> List[Dict]:
        """
        Scrape all projects from all pages
        """
        all_projects = []
        current_page = start_page
        # Get the first page to determine total pages
        first_page = self.get_page_content(start_page)
        if not first_page:
            return all_projects
        total_pages = self.get_total_pages(first_page)

        while current_page <= total_pages:
            if current_page == start_page:
                soup = first_page
            else:
                soup = self.get_page_content(current_page)
                if not soup:
                    continue
            # Find all project elements on the page
            project_elements = soup.find_all("div", class_="software-entry")

            for element in project_elements:
                project_data = self.parse_project(element)
                if project_data:
                    all_projects.append(project_data)
                    # Save each project immediately
                    self.save_to_jsonl([project_data], self.output_file, mode="a")

            current_page += 1
            # time.sleep(2)  # Be nice to the server
        return all_projects

    def save_to_jsonl(
        self,
        projects: List[Dict],
        filename: str = "devpost_projects.jsonl",
        mode: str = "w",
    ):
        """
        Save scraped projects to a JSONL file

        Args:
            projects: List of project dictionaries to save
            filename: Output filename
            mode: File open mode ('w' for write, 'a' for append)
        """
        try:
            with open(filename, mode, encoding="utf-8") as f:
                for project in projects:
                    json_line = json.dumps(project, ensure_ascii=False)
                    f.write(json_line + "\n")

            # if mode == 'w':
            #     print(f"Successfully saved {len(projects)} projects to {filename}")
            # elif mode == 'a':
            #     print(f"Successfully appended {len(projects)} projects to {filename}")
        except Exception as e:
            print(f"Error saving to JSONL: {e}")


def main():
    # file = "hackathons.csv"
    # df = pd.read_csv(file)
    # hackathons = df["hackathons"].tolist()
    hackathons = [
        # "nwhacks2016.devpost.com",
        # "nwhacks2017.devpost.com",
        # "nwhacks2018.devpost.com",
        # "nwhacks2019.devpost.com",
        # "nwhacks2020.devpost.com",
        # "nwhacks2021.devpost.com",
        # "nwhacks-2022.devpost.com",
        # "nwhacks-2023.devpost.com",
        # "nwhacks-2024.devpost.com",
        # "uottahack2019.devpost.com",
        # "uottahack3.devpost.com",
        # "uottahack-4.devpost.com", "uottahack5.devpost.com",
        # "hack-the-valley-4-9442.devpost.com",
        # "hack-the-valley-7.devpost.com",
        # "hack-the-valley-8.devpost.com",
        # "hack-the-valley-v.devpost.com",
        # "hack-the-valley-9.devpost.com",
        # "hackvalley.devpost.com",
        # "deerhacks.devpost.com",
        # "deerhacks-2023.devpost.com",
        # "deerhacks2024.devpost.com",
        # "https://makeuoft2019.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hawkhacks.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://makeuoft-2020.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://makeuoft-2021.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://makeuoft-2022.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://makeuoft-2023.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://makeuoft-2024.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehackswinter2015.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2016.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2017.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2018.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2019.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2020.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2021.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2022.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2023.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2024.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://treehacks-2017.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "uottahack-6.devpost.com",
        # "qhacks-2019.devpost.com",
        # "qhacks-2020.devpost.com",
        # "qhacks-2021.devpost.com",
        # "qhacks-2022.devpost.com",
        # "qhacks-2023.devpost.com",
        # "qhacks-2024.devpost.com",
        # "qhacks2016.devpost.com",
        # "qhacks2017.devpost.com",
        # "qhacks2018.devpost.com",
        # "https://yhack2014.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack2015.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack2016.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack2017.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack2019.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack2020.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack-2022.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://yhack.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit2014.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit-2016.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit2017.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit-2018.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hackmit-2019.devpost.com/?ref_feature=challenge&ref_medium=discover",
        # "https://hack-mit-2023.devpost.com/?ref_feature=challenge&ref_medium=discover",
    ]
# https://hackharvard2015.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard2016.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard-2017.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard2018.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard2019.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard21.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard2022.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard-2023.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackharvard-2024.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks15.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks16.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks-2017.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks2018.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks6.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks7.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks8.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks9.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks10.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://mchacks-11.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-fall16.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-spr17.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-fall17.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-f18.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-f19.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton21.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-spring-2022.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://hackprinceton-fall-2023.devpost.com/
# https://calhacks.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://cal-hacks2.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://calhacks4.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://cal-hacks-6.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://cal-hacks-8.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://calhacks90.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://cal-hacks-10.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://cal-hacks-11-0.devpost.com/?ref_feature=challenge&ref_medium=discover
# https://uc-berkeley-ai-hackathon-2024.devpost.com/
    output_file = "output/devpost_projects_bigredhacks_penapp.jsonl"
    hackathons = """https://bigredhacks.devpost.com/?ref_feature=challenge&ref_medium=discover
https://bigredhacks2015.devpost.com/?ref_feature=challenge&ref_medium=discover
https://brh2017.devpost.com/?ref_feature=challenge&ref_medium=discover
https://brhfa18.devpost.com/?ref_feature=challenge&ref_medium=discover
https://brhfa19.devpost.com/?ref_feature=challenge&ref_medium=discover
https://bigredhacks2021.devpost.com/?ref_feature=challenge&ref_medium=discover
https://bigred-hacks-2022.devpost.com/?ref_feature=challenge&ref_medium=discover
https://bigred-hacks-2024.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennappsxii.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xx.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xiv.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennappsxxi.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennappsx.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xviii.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xvii.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xvi.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xxv.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xxiv.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xxii.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xix.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps2015w.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps2014s.devpost.com/?ref_feature=challenge&ref_medium=discover
https://pennapps-xxiii.devpost.com/?ref_feature=challenge&ref_medium=discover
""".strip().split()

    for hackathon in tqdm(hackathons):
        domain = urlparse(hackathon).netloc
        scraper = DevPostScraper(
            base_url=f"https://{domain}/project-gallery", output_file=output_file
        )
        scraper.scrape_projects()


if __name__ == "__main__":
    main()
