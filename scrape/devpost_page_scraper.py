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
    # Example with proxy
    proxy = "123.45.67.89:8080"  # Replace with your proxy
    scraper = DevpostScraper(proxy=proxy)
    url = "https://devpost.com/software/notehacks-bsjdoi"
    result = scraper.scrape_submission(url)
    
    if result:
        # Save full data to JSONL
        with open('devpost_submissions.jsonl', 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # Save markdown separately for easy viewing
        with open('moonlit_description.md', 'w', encoding='utf-8') as f:
            f.write(result['description_markdown'])
            
        print("Description markdown content:")
        print(result['description_markdown'][:500] + "...")
        print("\nScraping completed successfully!")

if __name__ == "__main__":
    main()
