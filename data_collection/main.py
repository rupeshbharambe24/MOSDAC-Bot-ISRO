from crawler import MosdacCrawler
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting MOSDAC data extraction")
    crawler = MosdacCrawler()
    pdf_urls = [
        "https://www.mosdac.gov.in/docs/STQC.pdf",
        "https://www.mosdac.gov.in/sites/default/files/docs/INSAT_Product_Version_information_V01.pdf"
    ]
    for url in pdf_urls:
        crawler.process_url(url)
    crawler.run()
    logger.info("Extraction completed")

if __name__ == "__main__":
    main()