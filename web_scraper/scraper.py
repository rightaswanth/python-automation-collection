"""
Web Scraper CLI

Extracts data from a given URL based on provided CSS selectors.
Supports pagination, anti-block headers, and exports the scraped data to CSV or Excel.
"""

import argparse
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yaml
from typing import Dict, Any, List, Optional
import time
from urllib.parse import urljoin

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("web_scraper")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

class WebScraper:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.headers = {
            "User-Agent": self.config.get('scraper', {}).get('user_agent', 'Mozilla/5.0')
        }
        self.timeout = self.config.get('scraper', {}).get('timeout', 10)

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetches the HTML content of the page and returns a BeautifulSoup object."""
        try:
            self.logger.info(f"Fetching: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def parse_items(self, soup: BeautifulSoup, container_sel: str, title_sel: str, content_sel: str) -> List[Dict[str, str]]:
        """Parses the desired elements from the soup based on CSS selectors."""
        data = []
        containers = soup.select(container_sel)
        self.logger.info(f"Found {len(containers)} containers.")

        for container in containers:
            try:
                # Find title
                title_elem = container.select_one(title_sel)
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Check for link in title element if title element is <a> or contains <a>
                link = ""
                if title_elem and title_elem.name == 'a' and title_elem.has_attr('href'):
                     link = title_elem['href']
                elif title_elem and title_elem.find('a', href=True):
                     link = title_elem.find('a')['href']

                # Find content
                content_elem = container.select_one(content_sel)
                content = content_elem.get_text(strip=True) if content_elem else ""

                if title or content:
                    data.append({
                        "Title": title,
                        "Link": link,
                        "Content": content
                    })
            except Exception as e:
                self.logger.warning(f"Error parsing a container: {e}")

        return data

    def scrape(self, start_url: str, container_sel: str, title_sel: str, content_sel: str, max_pages: int = 1) -> pd.DataFrame:
        """Main scraping loop handling pagination if needed (basic NEXT link pagination)."""
        all_data = []
        current_url = start_url
        pages_scraped = 0

        while current_url and pages_scraped < max_pages:
            soup = self.fetch_page(current_url)
            if not soup:
                break

            items = self.parse_items(soup, container_sel, title_sel, content_sel)
            if not items:
                self.logger.info("No items found on this page, stopping.")
                break

            all_data.extend(items)
            pages_scraped += 1

            # Basic pagination logic looking for typical "Next" buttons
            # This is a generic approach; specific sites may need custom logic.
            next_button = soup.select_one('.next > a, a.next, a[rel="next"]')
            if next_button and next_button.has_attr('href'):
                # Handle relative URLs
                current_url = urljoin(current_url, next_button['href'])
                self.logger.info(f"Moving to next page: {current_url}")
                time.sleep(1) # Polite delay
            else:
                self.logger.info("No next page link found.")
                break

        self.logger.info(f"Scraping complete. Total items extracted: {len(all_data)}")
        return pd.DataFrame(all_data)


def main():
    parser = argparse.ArgumentParser(description="A generic web scraper using CSS selectors.")
    parser.add_argument("url", type=str, help="The URL to start scraping from.")
    parser.add_argument("--container", type=str, required=True, help="CSS selector for the item container.")
    parser.add_argument("--title", type=str, required=True, help="CSS selector for the title within the container.")
    parser.add_argument("--content", type=str, required=True, help="CSS selector for the content/price within the container.")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum number of pages to scrape.")
    parser.add_argument("--output", type=str, default="scraped_data.csv", help="Output file path (.csv or .xlsx).")

    args = parser.parse_args()

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'web_scraper.log'))

    scraper = WebScraper(config, logger)
    df = scraper.scrape(args.url, args.container, args.title, args.content, args.max_pages)

    if not df.empty:
        try:
            if args.output.endswith('.xlsx'):
                df.to_excel(args.output, index=False)
            else:
                df.to_csv(args.output, index=False)
            logger.info(f"Data saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    else:
        logger.warning("No data scraped. File not created.")

if __name__ == "__main__":
    main()
