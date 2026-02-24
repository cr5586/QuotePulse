import os
import time
import hashlib
import string
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self, headless=True, timeout=10, failure_dir='./artifacts/failures/'):
        self.headless = headless
        self.timeout = timeout
        self.failure_dir = failure_dir
        self.driver = None

    def _setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Selenium 4.10+ automatically manages the driver via Selenium Manager
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)

    def _normalize(self, text):
        # lowercasing and removing punctuation
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        return " ".join(text.split())

    def _generate_id(self, text, author):
        normalized_text = self._normalize(text)
        payload = f"{normalized_text}|{author}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def scrape(self, url="https://quotes.toscrape.com/js/", max_pages=None, run_id=None):
        if not self.driver:
            self._setup_driver()

        all_quotes = []
        pages_scraped = 0
        current_url = url

        try:
            while current_url:
                if max_pages and pages_scraped >= max_pages:
                    break
                
                logger.info(f"Scraping page: {current_url}")
                
                success = False
                for attempt in range(3):
                    try:
                        self.driver.get(current_url)
                        WebDriverWait(self.driver, self.timeout).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "quote"))
                        )
                        success = True
                        break
                    except (TimeoutException, Exception) as e:
                        logger.warning(f"Attempt {attempt + 1} failed for {current_url}: {e}")
                        if attempt == 2:
                            logger.error(f"Max retries reached for {current_url}")
                            self._capture_failure(run_id, pages_scraped)
                        else:
                            time.sleep(2) # Backoff

                if not success:
                    # User said: "Continue" if possible
                    # But if we can't load the page, we might be stuck or skip it
                    # Let's try to see if there's a next page even if this one failed? 
                    # Usually if the page failed to load, we can't find the next button.
                    # I'll try to find the next button anyway if it's there.
                    pass

                quotes = self.driver.find_elements(By.CLASS_NAME, "quote")
                if not quotes and success:
                    logger.warning(f"No quotes found on {current_url} even though it seemed to load.")

                for quote_el in quotes:
                    try:
                        text = quote_el.find_element(By.CLASS_NAME, "text").text
                        # Remove curly quotes if any
                        text = text.strip('“').strip('”')
                        
                        author = quote_el.find_element(By.CLASS_NAME, "author").text
                        
                        author_url = None
                        try:
                            # The link is usually next to the author name or inside an 'a' tag
                            # In quotes.toscrape.com/js, it's <small class="author">Author</small> <span><a href="/author/..."> (about)</a></span>
                            # Actually let's check the structure
                            author_link_el = quote_el.find_element(By.XPATH, ".//span/a[contains(@href, '/author/')]")
                            author_url = author_link_el.get_attribute("href")
                        except NoSuchElementException:
                            pass
                        
                        tags = [tag.text for tag in quote_el.find_elements(By.CLASS_NAME, "tag")]
                        
                        quote_id = self._generate_id(text, author)
                        
                        all_quotes.append({
                            "quote_id": quote_id,
                            "quote_text": text,
                            "author_name": author,
                            "author_url": author_url,
                            "tags": tags,
                            "page_url": current_url,
                            "scraped_at": datetime.utcnow().isoformat()
                        })
                    except (StaleElementReferenceException, NoSuchElementException) as e:
                        logger.warning(f"Error extracting quote: {e}")
                        continue

                pages_scraped += 1
                
                # Check for "Next" button
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "li.next a")
                    current_url = next_btn.get_attribute("href")
                except NoSuchElementException:
                    current_url = None

            return all_quotes, pages_scraped

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _capture_failure(self, run_id, page_num):
        if not run_id:
            run_id = "unknown"
        folder = os.path.join(self.failure_dir, run_id)
        os.makedirs(folder, exist_ok=True)
        
        timestamp = int(time.time())
        screenshot_path = f"{folder}/failure_page_{page_num}_{timestamp}.png"
        html_path = f"{folder}/failure_page_{page_num}_{timestamp}.html"
        
        try:
            self.driver.save_screenshot(screenshot_path)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Captured failure at {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to capture failure info: {e}")

    def navigate_with_retry(self, url, max_retries=3):
        # Implementation if I want more granular retries per navigation
        pass
