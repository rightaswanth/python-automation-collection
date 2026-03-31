# Web Scraper Module

Extract data dynamically from websites using custom CSS selectors. Features pagination, anti-block headers, and exports the scraped data to CSV or Excel formats.

## Features
- **URL Input**: Provide any starting URL.
- **Custom Selectors**: Use CSS selectors to pinpoint exactly what data you need (Container, Title, Content).
- **Pagination**: The scraper looks for standard "Next" buttons and automatically paginates up to your set limit.
- **Export Options**: Download results as CSV or Excel.

## Quick Start

### 1. Configuration
Open `config.yaml` to adjust the default timeouts, User-Agent headers, and default CSS selectors. Default settings are tuned for `books.toscrape.com`.

### 2. Streamlit Web Interface
Run the user-friendly interface:

```bash
cd python-automation-collection/web_scraper
streamlit run streamlit_app.py
```

### 3. Command Line Interface (CLI)
Run the scraping script from your terminal:

```bash
cd python-automation-collection/web_scraper
python scraper.py "http://books.toscrape.com/" --container "article.product_pod" --title "h3 > a" --content "p.price_color" --max-pages 2 --output "my_data.csv"
```

Logs will be saved to `web_scraper.log`.
