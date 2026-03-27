"""
PAA (People Also Ask) Scraper using undetected-chromedriver with manual stealth and human-like behavior.
Extracts 12+ PAA questions from Google search results.
"""

import asyncio
import os
import random
import re
import logging
import time
from dotenv import load_dotenv

load_dotenv()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("paa_scraper")

# Region-specific config
REGION_CONFIG = {
    "us": {
        "google_url": "https://www.google.com",
    },
    "india": {
        "google_url": "https://www.google.co.in",
    },
}

# CSS selectors for PAA question text extraction
PAA_QUESTION_SELECTORS = [
    'div[jsname="t779su"]', # Highly reliable question button
    'div[jsname="Cpkphb"]',
    'div.related-question-pair',
    'div[data-sgrd="true"]',
    'div[jsname="xXjONb"]',
    'div.ylgVCe',
    'span.CSkcDe',
    'span.qXOWAb',
    'div[jsname="yAnDWe"]',
    'div.dnXCYb',
    'div.wQ60Eb',
    'div.x6qLAd',
    'div.related-question-pair span',
    'div.dnXCYb span',
    'div.wQ60Eb span',
    'div[role="button"] span',
    'div[jsname="Cpkphb"] span',
    'div.cb748b',
    'div.K6p72',
]

def _random_delay(min_s: float = 1.0, max_s: float = 3.0):
    """Introduce a random human-like delay."""
    time.sleep(random.uniform(min_s, max_s))


def _human_type(driver, element, text: str):
    """Type text character by character with random delays to mimic a human."""
    element.click()
    for char in text:
        element.send_keys(char)
        time.sleep(random.randint(80, 200) / 1000.0)
    _random_delay(0.5, 1.5)


def _smooth_scroll(driver, distance: int = 500):
    """Scroll the page smoothly like a human."""
    steps = random.randint(3, 6)
    step_distance = distance // steps
    for _ in range(steps):
        driver.execute_script(f"window.scrollBy(0, {step_distance});")
        time.sleep(random.uniform(0.1, 0.3))


def _clean_question(text: str) -> str | None:
    """Clean and validate a question string. Returns None if invalid."""
    if not text:
        return None

    lower = text.lower()

    # --- PHASE 1: Reject obvious junk before any processing ---
    junk_phrases = [
        "can't generate", "ai overview", "try again later",
        "people also ask", "more results", "about featured snippets",
        "send feedback", "table of contents", "'s post",
    ]
    if any(j in lower for j in junk_phrases):
        return None

    # Reject text with emojis
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0000200D\U000023F0-\U000023FA]",
        flags=re.UNICODE
    )
    if emoji_pattern.search(text):
        return None

    # Reject hashtags
    if re.search(r"#\w+", text):
        return None

    # Reject truncated snippets
    stripped = text.rstrip()
    if stripped.endswith("...") or stripped.endswith("…"):
        return None

    # Reject text starting with a date
    if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\w*\.?\s+\d", text, re.IGNORECASE):
        return None

    # Reject text containing URLs
    if re.search(r"https?://|www\.", text):
        return None

    # Reject text with too many special characters
    special_count = sum(1 for c in text if c in "@#$%^&*{}[]<>~`|\\")
    if special_count > 2:
        return None

    # Reject text ending with colon
    if stripped.endswith(":"):
        return None

    # Reject FAQ-style content with " * " bullets
    if " * " in text and "?" in text:
        return None

    # Reject text starting with "Solved]" or containing bracket junk
    if re.match(r"^\[?Solved\]", text, re.IGNORECASE):
        return None

    # Reject "Ask SiteName -" prefixed text
    if re.match(r"^Ask\s+\w+\s*[-—–]", text, re.IGNORECASE):
        return None

    # --- PHASE 2: Extract a clean question ---
    if "?" in text:
        q = text[: text.index("?") + 1].strip()
        while q and not q[0].isalpha():
            q = q[1:].strip()
        q_lower = q.lower()
        if _is_non_paa_question(q_lower):
            return None
        if len(q) >= 15:
            return q

    # Strip trailing page titles
    for sep in [" | ", " - ", " — ", " – "]:
        if sep in text:
            text = text[:text.index(sep)].strip()
            lower = text.lower()

    # If it reached here, it didn't start with a question word.
    # But it might still be a valid question if it ends with ?
    if "?" in text:
        q = text.strip()
        # Clean up some common junk after the question
        if " · " in q:
            q = q.split(" · ")[0].strip()
        if len(q) >= 15 and len(q) <= 200:
            return q

    # Final attempt: if it's a reasonable length and looks like a question
    if 20 <= len(text) <= 150 and not any(j in lower for j in ["search", "results", "feedback"]):
         return text.strip()

    return None


def _is_non_paa_question(text_lower: str) -> bool:
    """Return True if text looks like a non-PAA snippet."""
    non_paa_patterns = [
        r'^how to say\b.*\bin\b', r'^how to maximize\b', r'^how to master\b',
        r'^how to become\b', r'^how they work\b', r'^why we picked\b',
        r'^why these\b', r'^top \d+\b', r"^when it'?s\b",
        r'^i plan on\b', r"^i'm curious\b", r'^different types of\b',
        r'^types of\b', r'^ethics and\b',
    ]
    for pattern in non_paa_patterns:
        if re.match(pattern, text_lower):
            return True
    return False


def _extract_paa_questions(driver) -> list[str]:
    """Extract all visible PAA question texts from the page."""
    questions = set()

    for selector in PAA_QUESTION_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    if not el.is_displayed():
                        continue
                    text = el.get_attribute("textContent").strip()
                    if not text:
                        continue
                    
                    cleaned = _clean_question(text)
                    if cleaned:
                        questions.add(cleaned)
                    else:
                        if len(text) > 20: # Log potentially missed questions
                            logger.debug(f"      Rejected text: {text[:50]}...")
                except Exception:
                    continue
        except Exception:
            continue

    if not questions:
        # Fallback: try finding all buttons in the PAA area
        try:
            # Look for elements that look like accordion headers
            headers = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"][aria-expanded]')
            for h in headers:
                text = h.get_attribute("textContent").strip()
                cleaned = _clean_question(text)
                if cleaned:
                    questions.add(cleaned)
        except Exception:
            pass

    return list(questions)


def _find_and_click_paa(driver, already_clicked: set) -> int:
    """Find PAA accordion items and click unexpanded ones. Returns count of new clicks."""
    clicks = 0

    clickable_selectors = [
        'div[jsname="Cpkphb"]',
        'div.related-question-pair',
        'div[data-sgrd="true"]',
        'div[jsname="xXjONb"]',
        'div[jsname="yAnDWe"]',
        'div.dnXCYb',
        'div.wQ60Eb',
        'div.x6qLAd',
    ]

    for selector in clickable_selectors:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            for item in items:
                try:
                    text = item.get_attribute("textContent").strip()
                    if not text:
                        continue
                        
                    # Extract just the question part for reliable already_clicked tracking
                    question_text = text.split('?')[0] + '?' if '?' in text else text[:80]
                    if question_text in already_clicked:
                        continue

                    if not item.is_displayed():
                        continue

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                    _random_delay(0.3, 0.8)

                    click_success = False
                    try:
                        inner = item.find_element(By.CSS_SELECTOR, '[aria-expanded="false"]')
                        if inner:
                            driver.execute_script("arguments[0].click();", inner)
                            click_success = True
                    except Exception:
                        pass
                        
                    if not click_success:
                        driver.execute_script("arguments[0].click();", item)

                    already_clicked.add(question_text)
                    clicks += 1
                    _random_delay(1.5, 3.0)

                    if clicks >= 3:
                        return clicks
                except Exception:
                    continue
                    
            if clicks > 0:
                break
        except Exception:
            continue

    return clicks


def _scrape_paa_with_driver(driver, keyword: str, region: str = "us", google_url: str = "https://www.google.com") -> dict:
    """
    Extract PAA questions for a single keyword using an already running driver.
    """
    try:
        # Navigate to Google search for the keyword
        # If we are already on a search page, we can just use the search box there
        search_selectors = [
            'textarea[name="q"]', 'input[name="q"]',
            'textarea[title="Search"]', 'input[title="Search"]',
        ]
        
        search_box = None
        for sel in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                if elements and elements[0].is_displayed():
                    search_box = elements[0]
                    break
            except Exception:
                continue

        if not search_box:
            # Try navigating to google home if search box not found
            driver.get(google_url)
            _random_delay(2.0, 4.0)
            for sel in search_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements and elements[0].is_displayed():
                        search_box = elements[0]
                        break
                except Exception:
                    continue

        if not search_box:
             return {"keyword": keyword, "region": region, "error": "Could not find Google search box"}

        # Clear existing text if any
        search_box.click()
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.BACKSPACE)
        _random_delay(0.5, 1.0)
        
        _human_type(driver, search_box, keyword)
        search_box.send_keys(Keys.ENTER)
        _random_delay(5.0, 10.0) # Increased wait for search results

        # Wait for search results or PAA specifically
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#search, .related-question-pair, div[jsname='Cpkphb']"))
            )
        except Exception:
            pass

        # Scroll down to find PAA section - do it in multiple small steps
        for _ in range(3):
            _smooth_scroll(driver, random.randint(300, 500))
            _random_delay(1.0, 2.0)
            
        # Extra wait for PAA to settle
        _random_delay(2.0, 4.0)

        # Recursive PAA expansion loop
        all_questions = []
        already_clicked = set()
        max_rounds = 15
        no_new_count = 0

        for round_num in range(max_rounds):
            logger.info(f"  Round {round_num + 1}: extracting questions...")
            try:
                driver.title
            except Exception:
                logger.warning("  Browser closed unexpectedly, returning what we have.")
                break

            current_questions = _extract_paa_questions(driver)
            new_count = 0
            for q in current_questions:
                if q not in all_questions:
                    all_questions.append(q)
                    new_count += 1

            logger.info(f"  Found {new_count} new questions (total: {len(all_questions)})")

            if len(all_questions) >= 16:
                logger.info(f"  Reached 16+ questions, stopping.")
                break

            # Try clicking to expand more PAA items
            try:
                clicks = _find_and_click_paa(driver, already_clicked)
            except Exception as e:
                logger.warning(f"  Click error: {e}")
                clicks = 0

            if clicks == 0 and new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    logger.info(f"  No new questions found for 3 rounds, stopping.")
                    break
                try:
                    _smooth_scroll(driver, random.randint(300, 600))
                    _random_delay(1.5, 3.0)
                except Exception:
                    break
            else:
                no_new_count = 0

            _random_delay(1.0, 2.0)

        return {
            "keyword": keyword,
            "region": region,
            "questions": all_questions[:16],
            "count": min(len(all_questions), 16),
        }
    except Exception as e:
        logger.error(f"Error scraping PAA for '{keyword}': {e}")
        return {"keyword": keyword, "region": region, "error": str(e)}


def _scrape_paa_sync(keyword: str, region: str = "us") -> dict:
    """
    Synchronous PAA scraper using undetected-chromedriver.
    """
    region = region.lower().strip()
    if region not in REGION_CONFIG:
        return {"keyword": keyword, "region": region, "error": f"Unsupported region: {region}. Use 'us' or 'india'."}

    config = REGION_CONFIG[region]
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    logger.info(f"Scraping PAA for '{keyword}' in region '{region}' (headless={headless}, DISPLAY={os.getenv('DISPLAY')})")

    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    else:
        # Ensure window is visible and focused
        options.add_argument("--start-maximized")
        options.add_argument("--force-device-scale-factor=1")

    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    
    # Persistent user data directory
    user_data_dir = os.path.join(os.getcwd(), "browser_data")

    driver = None
    try:
        logger.info(f"  Attempting to start Chrome driver (headless={headless})...")
        driver = uc.Chrome(
            options=options,
            user_data_dir=user_data_dir,
            use_subprocess=False
        )
        logger.info("  ✅ Chrome driver started successfully.")
        
        if not headless:
            driver.set_window_size(1366, 768)
            driver.set_window_position(0, 0)
            _random_delay(1.0, 2.0) # Wait for window to appear
        
        driver.set_page_load_timeout(60)
        
        # Navigate to Google
        try:
            driver.get(config["google_url"])
        except Exception as e:
            logger.warning(f"Timeout loading {config['google_url']}, continuing anyway: {e}")
            
        _random_delay(3.0, 6.0)

        # Handle cookie consent if present
        try:
            consent_btn = driver.find_elements(By.XPATH, '//button[contains(text(), "Accept all")]')
            if consent_btn:
                consent_btn[0].click()
                _random_delay(1.0, 2.0)
        except Exception:
            pass

        # Check for CAPTCHA ("Unusual traffic" from Google)
        page_source = driver.page_source.lower()
        captcha_indicators = [
            "not a robot", "unusual traffic", "challenge", "captcha", 
            "validate your request", "automated requests"
        ]
        if any(indicator in page_source for indicator in captcha_indicators):
            logger.warning("  🚨 CAPTCHA DETECTED! Please solve it manually in the browser window within 60 seconds.")
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="q"], input[name="q"]'))
                )
                logger.info("  ✅ CAPTCHA solved! Resuming scraping.")
                _random_delay(2.0, 4.0)
            except Exception:
                driver.quit()
                return {"keyword": keyword, "region": region, "error": "CAPTCHA not solved in time. Please try again."}

        # Perform extraction
        result = _scrape_paa_with_driver(driver, keyword, region, config["google_url"])
        
        try:
            driver.quit()
        except:
            pass

        return result
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        logger.error(f"Error scraping PAA for '{keyword}': {e}")
        return {"keyword": keyword, "region": region, "error": str(e)}


def scrape_batch_sync(keywords: list[str], region: str = "us", callback=None) -> list[dict]:
    """
    Scrape multiple keywords in a single browser session.
    Optional callback(result_dict) is called after each keyword.
    """
    region = region.lower().strip()
    if region not in REGION_CONFIG:
        error_results = [{"keyword": k, "region": region, "error": f"Unsupported region: {region}"} for k in keywords]
        if callback:
            for er in error_results:
                callback(er)
        return error_results

    config = REGION_CONFIG[region]
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    logger.info(f"Batch scraping {len(keywords)} keywords in region '{region}' (headless={headless}, DISPLAY={os.getenv('DISPLAY')})")

    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    else:
        options.add_argument("--start-maximized")
        options.add_argument("--force-device-scale-factor=1")

    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")
    
    user_data_dir = os.path.join(os.getcwd(), "browser_data")

    results = []
    driver = None
    try:
        logger.info(f"  Attempting to start Chrome driver (headless={headless})...")
        driver = uc.Chrome(options=options, user_data_dir=user_data_dir, use_subprocess=False)
        logger.info("  ✅ Chrome driver started successfully.")
        
        if not headless:
            driver.set_window_size(1366, 768)
            driver.set_window_position(0, 0)
            _random_delay(1.0, 2.0)

        driver.set_page_load_timeout(60)
        
        try:
            driver.get(config["google_url"])
        except Exception as e:
            logger.warning(f"Timeout loading {config['google_url']}: {e}")
            
        _random_delay(3.0, 6.0)

        # Handle cookie consent if present
        try:
            consent_btn = driver.find_elements(By.XPATH, '//button[contains(text(), "Accept all")]')
            if consent_btn:
                consent_btn[0].click()
                _random_delay(1.0, 2.0)
        except Exception:
            pass

        for i, keyword in enumerate(keywords):
            logger.info(f"Processing keyword {i+1}/{len(keywords)}: '{keyword}'")
            
            # Check for CAPTCHA before each keyword if necessary, or just rely on the keyword's try block
            page_source = driver.page_source.lower()
            captcha_indicators = ["not a robot", "unusual traffic", "challenge", "captcha"]
            if any(indicator in page_source for indicator in captcha_indicators):
                logger.warning("  🚨 CAPTCHA DETECTED! Waiting up to 60s for manual solution.")
                try:
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="q"], input[name="q"]'))
                    )
                    logger.info("  ✅ CAPTCHA solved!")
                except Exception:
                    logger.error("  ❌ CAPTCHA not solved, skipping remaining keywords.")
                    break

            result = _scrape_paa_with_driver(driver, keyword, region, config["google_url"])
            results.append(result)
            
            if callback:
                try:
                    callback(result)
                except Exception as cb_e:
                    logger.error(f"Callback error for '{keyword}': {cb_e}")
            
            # Save progress or yield if needed? For now just append.
            # Random delay between keywords
            if i < len(keywords) - 1:
                delay = random.uniform(5.0, 12.0)
                logger.info(f"  Waiting {delay:.1f}s before next keyword...")
                time.sleep(delay)

        driver.quit()
    except Exception as e:
        logger.error(f"Fatal error in batch scrape: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return results


async def scrape_multiple(keywords: list[str], region: str = "us") -> list[dict]:
    """
    Scrape PAA questions for multiple keywords using the batch logic (single browser session).
    """
    return await asyncio.to_thread(scrape_batch_sync, keywords, region)


async def scrape_multiple_with_callback(keywords: list[str], region: str, callback) -> list[dict]:
    """
    Async wrapper for batch scraping with a callback.
    """
    return await asyncio.to_thread(scrape_batch_sync, keywords, region, callback)
