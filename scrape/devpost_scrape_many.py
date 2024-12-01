import json
import multiprocessing as mp
from tqdm import tqdm
import random
import time
import logging
import time

def process_project(project):
    """Process a single project"""
    scraper = DevpostScraper()
    try:
        url = project.get('project_url')
        if not url:
            return None
            
        parsed_content = scraper.scrape_submission(url)
        if parsed_content:
            project['parsed_content'] = parsed_content
            return project
            
    except Exception as e:
        logging.error(f"Error processing {url}: {str(e)}")
    
    time.sleep(random.random()*5)
    
    return None

import requests
import re
from bs4 import BeautifulSoup
import json
import time
import logging
from markdownify import markdownify as md

class DevpostScraper:
    def __init__(self, proxy=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.proxy = proxy
        
        # Format proxy dictionary if proxy is provided
        self.proxies = None
        if self.proxy:
            if not self.proxy.startswith(('http://', 'https://')):
                self.proxy = 'http://' + self.proxy
            self.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
            self.logger.info(f"Using proxy: {self.proxy}")

    def clean_markdown(self, content):
        """Clean up markdown content by removing excessive newlines"""
        # Replace 3 or more newlines with 2 newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', content)
        # Remove spaces before newlines
        cleaned = re.sub(r' +\n', '\n', cleaned)
        return cleaned.strip()

    def scrape_description(self, soup):
        """Extract project description and convert to Markdown"""
        # Find gallery div
        gallery_div = soup.find('div', {'id': 'gallery'})
        if not gallery_div:
            return ""
        
        # Get the next sibling div which contains the description
        description_div = gallery_div.find_next_sibling('div')
        if not description_div:
            return ""
        
        # Convert to Markdown using markdownify
        markdown_content = md(str(description_div), heading_style="ATX")
        cleaned_content = self.clean_markdown(markdown_content)
        return cleaned_content

    def scrape_submission(self, url):
        try:
            # Add timeout and proxy configuration
            response = requests.get(
                url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=30  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get project description
            markdown_description = self.scrape_description(soup)
            
            # Get technologies used
            built_with = []
            tech_section = soup.find('div', {'id': 'built-with'})
            if tech_section:
                built_with = [tag.text.strip() for tag in tech_section.find_all('span', {'class': 'cp-tag'})]
            
            # Get links
            links = []
            links_section = soup.find('nav', {'class': 'app-links'})
            if links_section:
                for link in links_section.find_all('a'):
                    links.append({
                        'title': link.get('title'),
                        'url': link.get('href')
                    })
            
            # Get submission info
            submissions = []
            submissions_section = soup.find('div', {'id': 'submissions'})
            if submissions_section:
                hackathon_link = submissions_section.find('a')
                if hackathon_link:
                    hackathon_info = {
                        'name': hackathon_link.text.strip(),
                        'url': hackathon_link.get('href'),
                        'awards': []
                    }
                    winner_labels = submissions_section.find_all('span', {'class': 'winner'})
                    for label in winner_labels:
                        award_text = label.find_next_sibling(text=True)
                        if award_text:
                            hackathon_info['awards'].append(award_text.strip())
                    submissions.append(hackathon_info)
            
            data = {
                'url': url,
                'description_markdown': markdown_description,
                'built_with': built_with,
                'links': links,
                'submissions': submissions,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error scraping {url}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='scraping.log'
    )
    
    # Load projects
    files = ["output/devpost_projects_bigredhacks_penapp.jsonl"]
    projects = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            projects.extend([json.loads(line) for line in f.readlines()])
    
    projects = projects[1538:]
    output_file = 'output/projects_parsed.jsonl'
    
    num_cores = mp.cpu_count()
    pool = mp.Pool(num_cores)
    
    # Process projects
    projects.reverse()
    print(f"Processing {len(projects)} projects using {num_cores} cores...")
    
    with open(output_file, 'a', encoding='utf-8') as f:
        for result in tqdm(pool.imap(process_project, projects), total=len(projects)):
            if result:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    pool.close()
    pool.join()
    
    print(f"\nProcessing complete. Results saved to {output_file}")
    print(f"Check scraping.log for any errors.")

if __name__ == "__main__":
    main()
