"""
Streamlit Web App for Web Scraper Module

A user-friendly interface to input URLs and CSS selectors, scrape data,
view progress, and download the results as CSV or Excel.
"""

import streamlit as st
import pandas as pd
import yaml
import logging
from io import BytesIO
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import time

# Set up page config
st.set_page_config(page_title="Web Scraper", page_icon="🕸️", layout="wide")

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("web_scraper_ui")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def load_config() -> dict:
    try:
        with open("config.yaml", 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Failed to load config file: {e}")
        return {}

def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Scraped Data')
    return output.getvalue()

def scrape_data(start_url: str, container_sel: str, title_sel: str, content_sel: str, max_pages: int, config: dict, logger: logging.Logger):
    """
    Scrapes data and updates a Streamlit progress bar.
    """
    all_data = []
    current_url = start_url
    pages_scraped = 0

    headers = {"User-Agent": config.get('scraper', {}).get('user_agent', 'Mozilla/5.0')}
    timeout = config.get('scraper', {}).get('timeout', 10)

    progress_bar = st.progress(0)
    status_text = st.empty()

    while current_url and pages_scraped < max_pages:
        status_text.text(f"Scraping page {pages_scraped + 1} of {max_pages}: {current_url}")
        try:
            response = requests.get(current_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {current_url}: {e}")
            st.error(f"Error fetching URL: {e}")
            break

        containers = soup.select(container_sel)

        for container in containers:
            try:
                title_elem = container.select_one(title_sel)
                title = title_elem.get_text(strip=True) if title_elem else ""

                link = ""
                if title_elem and title_elem.name == 'a' and title_elem.has_attr('href'):
                     link = title_elem['href']
                elif title_elem and title_elem.find('a', href=True):
                     link = title_elem.find('a')['href']

                content_elem = container.select_one(content_sel)
                content = content_elem.get_text(strip=True) if content_elem else ""

                if title or content:
                    all_data.append({"Title": title, "Link": urljoin(current_url, link) if link else "", "Content": content})
            except Exception as e:
                logger.warning(f"Error parsing item: {e}")

        pages_scraped += 1
        progress_bar.progress(pages_scraped / max_pages)

        next_button = soup.select_one('.next > a, a.next, a[rel="next"]')
        if next_button and next_button.has_attr('href'):
            current_url = urljoin(current_url, next_button['href'])
            time.sleep(1) # Polite delay
        else:
            status_text.text("No more pages found.")
            break

    progress_bar.progress(1.0)
    status_text.text("Scraping complete!")
    return pd.DataFrame(all_data)

def main():
    st.title("🕸️ Web Scraper")
    st.markdown("Extract data from websites using CSS selectors. Features pagination and anti-block headers.")

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'web_scraper.log'))

    # Sidebar Configuration
    st.sidebar.header("⚙️ Scraping Settings")
    st.sidebar.markdown("Use CSS selectors to target elements. For example, `h3 > a` targets a link inside an `h3` tag.")

    start_url = st.sidebar.text_input("Start URL", value="http://books.toscrape.com/")
    container_sel = st.sidebar.text_input("Container Selector", value=config.get('scraper', {}).get('default_container_selector', 'article.product_pod'))
    title_sel = st.sidebar.text_input("Title Selector", value=config.get('scraper', {}).get('default_title_selector', 'h3 > a'))
    content_sel = st.sidebar.text_input("Content Selector (e.g., Price/Description)", value=config.get('scraper', {}).get('default_content_selector', 'p.price_color'))

    max_pages = st.sidebar.number_input("Max Pages to Scrape", min_value=1, max_value=100, value=config.get('scraper', {}).get('max_pages', 5))

    # Main Area
    st.write("### Instructions")
    st.write("1. Enter the starting URL in the sidebar.\n2. Provide the CSS selectors that match the data structure on the website.\n3. Click 'Start Scraping'.")

    if st.button("🚀 Start Scraping"):
        if not start_url or not container_sel or not title_sel or not content_sel:
            st.error("Please fill in all URL and selector fields.")
        else:
            with st.spinner("Initializing scraper..."):
                df = scrape_data(start_url, container_sel, title_sel, content_sel, max_pages, config, logger)

                if not df.empty:
                    st.success(f"Successfully scraped {len(df)} items!")
                    st.write("### Data Preview")
                    st.dataframe(df.head(10))

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download CSV",
                            data=convert_df_to_csv(df),
                            file_name="scraped_data.csv",
                            mime="text/csv"
                        )
                    with col2:
                        st.download_button(
                            label="📥 Download Excel",
                            data=convert_df_to_excel(df),
                            file_name="scraped_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("No data was scraped. Please check your CSS selectors and URL.")

if __name__ == "__main__":
    main()
