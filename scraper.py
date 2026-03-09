"""
PAA (People Also Ask) Scraper using Playwright with manual stealth and human-like behavior.
Extracts 12+ PAA questions from Google search results.
"""

import asyncio
import os
import random
import re
import logging

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("paa_scraper")

# Pool of realistic Chrome user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Region-specific config
REGION_CONFIG = {
    "us": {
        "google_url": "https://www.google.com",
        "timezone": "America/New_York",
        "locale": "en-US",
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
    },
    "india": {
        "google_url": "https://www.google.co.in",
        "timezone": "Asia/Kolkata",
        "locale": "en-IN",
        "geolocation": {"latitude": 28.6139, "longitude": 77.2090},
    },
}

# CSS selectors for PAA question text extraction
PAA_QUESTION_SELECTORS = [
    'div[jsname="Cpkphb"] span',
    'div.related-question-pair span',
    'div[data-sgrd="true"] span',
    'div[jsname="xXjONb"] span',
    'div.ylgVCe',
    'span.CSkcDe',
]

# Stealth JavaScript to inject before page loads
STEALTH_SCRIPTS = [
    """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    """,
    """
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ],
    });
    """,
    """
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    """,
    """
    window.chrome = {
        runtime: {},
    };
    """,
    """
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """,
]


async def _apply_stealth(page):
    """Apply stealth patches to evade bot detection."""
    for script in STEALTH_SCRIPTS:
        await page.add_init_script(script)


async def _random_delay(min_s: float = 1.0, max_s: float = 3.0):
    """Introduce a random human-like delay."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _human_type(page, selector: str, text: str):
    """Type text character by character with random delays to mimic a human."""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char, delay=random.randint(80, 200))
    await _random_delay(0.5, 1.5)


async def _smooth_scroll(page, distance: int = 500):
    """Scroll the page smoothly like a human."""
    steps = random.randint(3, 6)
    step_distance = distance // steps
    for _ in range(steps):
        await page.mouse.wheel(0, step_distance)
        await asyncio.sleep(random.uniform(0.1, 0.3))


def _clean_question(text: str) -> str | None:
    """Clean and validate a question string. Returns None if invalid."""
    if not text:
        return None

    lower = text.lower()

    # --- PHASE 1: Reject obvious junk before any processing ---

    # Skip known non-question content
    junk_phrases = [
        "can't generate", "ai overview", "try again later",
        "people also ask", "more results", "about featured snippets",
        "send feedback", "table of contents", "'s post",
    ]
    if any(j in lower for j in junk_phrases):
        return None

    # Reject text with emojis (social media posts / bios)
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U0000FE00-\U0000FE0F"
        "\U0000200D"
        "\U000023F0-\U000023FA"
        "]", flags=re.UNICODE
    )
    if emoji_pattern.search(text):
        return None

    # Reject hashtags (#Author, #Zomato, etc.)
    if re.search(r"#\w+", text):
        return None

    # Reject truncated snippets (ending with "..." or "…")
    stripped = text.rstrip()
    if stripped.endswith("...") or stripped.endswith("…"):
        return None

    # Reject text starting with a date (e.g., "May 2021 —", "Jan 2024 —", "Sept 2025 —")
    if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\w*\.?\s+\d", text, re.IGNORECASE):
        return None

    # Reject text containing URLs
    if re.search(r"https?://|www\.", text):
        return None

    # Reject text with too many special characters
    special_count = sum(1 for c in text if c in "@#$%^&*{}[]<>~`|\\")
    if special_count > 2:
        return None

    # Reject text ending with colon (incomplete phrases like "What takes longer:", "Why these jobs are resilient:")
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

    # If text contains a '?', extract just the question part (first sentence ending with ?)
    if "?" in text:
        q = text[: text.index("?") + 1].strip()
        # Clean leading junk like bullet points, numbers, or special chars
        while q and not q[0].isalpha():
            q = q[1:].strip()
        # Re-check: reject if it's a quirky non-PAA question
        q_lower = q.lower()
        if _is_non_paa_question(q_lower):
            return None
        if len(q) >= 15:
            return q

    # Strip trailing page titles (e.g., "What is SEO | Some Website")
    for sep in [" | ", " - ", " — ", " – "]:
        if sep in text:
            text = text[:text.index(sep)].strip()
            lower = text.lower()

    # Check if it starts with a question word (sometimes Google omits the ?)
    question_words = [
        "what", "how", "why", "when", "where", "who",
        "which", "is", "are", "can", "do", "does",
        "will", "should", "could", "would",
    ]
    if any(lower.startswith(w + " ") for w in question_words):
        first_line = text.split("\n")[0].strip()
        if _is_non_paa_question(first_line.lower()):
            return None
        if 15 <= len(first_line) <= 150:
            return first_line

    return None


def _is_non_paa_question(text_lower: str) -> bool:
    """Return True if text looks like a non-PAA snippet (headline, life advice, how-to title, etc.)."""
    # Reject vague/chatty phrases that aren't real PAA questions
    non_paa_patterns = [
        r'^how to say\b.*\bin\b',           # "How to say I love you in C++"
        r'^how to maximize\b',               # "How to maximize your 2 days"
        r'^how to master\b',                 # "How to Master DSA in 3 Months"
        r'^how to become\b',                 # "How to become a content writer"
        r'^how they work\b',                 # "How they work together"
        r'^why we picked\b',                 # "Why We Picked It"
        r'^why these\b',                     # "Why these jobs are resilient"
        r'^top \d+\b',                       # "Top 10 AI companies ranked"
        r"^when it'?s\b",                    # "When it's Illegal"
        r'^i plan on\b',                     # "I plan on putting 3 months..."
        r"^i'm curious\b",                   # "I'm curious, what does..."
        r'^different types of\b',            # "Different Types Of Writers"
        r'^types of\b',                      # "Types of Writers"
        r'^ethics and\b',                    # "Ethics and AI Phone Calls"
    ]
    for pattern in non_paa_patterns:
        if re.match(pattern, text_lower):
            return True
    return False


async def _extract_paa_questions(page) -> list[str]:
    """Extract all visible PAA question texts from the page."""
    questions = set()

    for selector in PAA_QUESTION_SELECTORS:
        try:
            elements = await page.query_selector_all(selector)
            for el in elements:
                try:
                    text = (await el.inner_text()).strip()
                    if not text or len(text) < 10 or len(text) > 300:
                        continue
                    cleaned = _clean_question(text)
                    if cleaned:
                        questions.add(cleaned)
                except Exception:
                    continue
        except Exception:
            continue

    return list(questions)


async def _find_and_click_paa(page, already_clicked: set) -> int:
    """Find PAA accordion items and click unexpanded ones. Returns count of new clicks."""
    clicks = 0

    clickable_selectors = [
        'div[jsname="Cpkphb"]',
        'div.related-question-pair',
        'div[data-sgrd="true"]',
        'div[jsname="xXjONb"]',
    ]

    for selector in clickable_selectors:
        try:
            items = await page.query_selector_all(selector)
            for item in items:
                try:
                    text = (await item.inner_text()).strip()
                    short_text = text[:80]
                    if short_text in already_clicked:
                        continue

                    is_visible = await item.is_visible()
                    if not is_visible:
                        continue

                    await item.scroll_into_view_if_needed()
                    await _random_delay(0.3, 0.8)

                    # Use force click to avoid navigation issues
                    try:
                        await item.click(timeout=5000)
                    except Exception:
                        # Try clicking the aria-expanded element inside
                        try:
                            inner = await item.query_selector('[aria-expanded]')
                            if inner:
                                await inner.click(timeout=5000)
                        except Exception:
                            continue

                    already_clicked.add(short_text)
                    clicks += 1

                    await _random_delay(1.5, 3.0)

                    if clicks >= 3:
                        return clicks
                except Exception:
                    continue
        except Exception:
            continue

    return clicks


async def scrape_paa(keyword: str, region: str = "us") -> dict:
    """
    Scrape Google PAA questions for a given keyword and region.
    Returns dict with keyword, region, questions list, and count.
    """
    region = region.lower().strip()
    if region not in REGION_CONFIG:
        return {"keyword": keyword, "region": region, "error": f"Unsupported region: {region}. Use 'us' or 'india'."}

    config = REGION_CONFIG[region]
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    # Support multiple proxies via PROXY_URLS (comma-separated) or single PROXY_URL
    proxy_urls_str = os.getenv("PROXY_URLS", "") or os.getenv("PROXY_URL", "")
    proxy_list = [u.strip() for u in proxy_urls_str.split(",") if u.strip()] if proxy_urls_str else []
    
    # Pick a random proxy from the list for this attempt
    proxy = None
    if proxy_list:
        chosen = random.choice(proxy_list)
        proxy = {"server": chosen}
        logger.info(f"  Using proxy: {chosen.split('@')[-1] if '@' in chosen else chosen}")

    logger.info(f"Scraping PAA for '{keyword}' in region '{region}' (headless={headless})")

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                channel="chrome",
                proxy=proxy,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1366,768",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=random.choice(USER_AGENTS),
                locale=config["locale"],
                timezone_id=config["timezone"],
                geolocation=config["geolocation"],
                permissions=["geolocation"],
            )

            page = await context.new_page()
            page.set_default_timeout(60000)

            # Apply stealth patches
            await _apply_stealth(page)

            # Navigate to Google - Use "commit" and higher timeout for slow proxies
            await page.goto(config["google_url"], wait_until="commit", timeout=60000)
            await _random_delay(2.0, 4.0)

            # Handle cookie consent if present
            try:
                consent_btn = page.locator('button:has-text("Accept all")')
                if await consent_btn.count() > 0:
                    await consent_btn.first.click()
                    await _random_delay(1.0, 2.0)
            except Exception:
                pass

            # Check for CAPTCHA or "Unusual traffic"
            content = await page.content()
            captcha_indicators = [
                "not a robot", "unusual traffic", "challenge", "captcha", 
                "validate your request", "automated requests"
            ]
            if any(indicator in content.lower() for indicator in captcha_indicators):
                await browser.close()
                return {"keyword": keyword, "region": region, "error": "CAPTCHA or bot detection triggered by Google"}

            # Find the search box and type the keyword - added more selectors for resilience
            search_selectors = [
                'textarea[name="q"]', 
                'input[name="q"]',
                'textarea[title="Search"]',
                'input[title="Search"]',
                '.gLFyf' # Common search class
            ]
            typed = False
            for sel in search_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.count() > 0 and await el.is_visible():
                        await el.click() # Click first to focus
                        await _human_type(page, sel, keyword)
                        typed = True
                        break
                except Exception:
                    continue

            if not typed:
                # Last resort check: if we are at the search results already (maybe from an earlier redirect)
                if "search?" in page.url:
                    logger.info("  Already on search results page, skipping typing.")
                    typed = True
                else:
                    # Diagnose what Google is showing
                    try:
                        page_title = await page.title()
                        page_url = page.url
                        body_text = await page.inner_text("body")
                        snippet = body_text[:300].replace('\n', ' ')
                        logger.error(f"  DIAGNOSTIC — Page title: '{page_title}', URL: '{page_url}'")
                        logger.error(f"  DIAGNOSTIC — Body snippet: {snippet}")
                    except Exception:
                        pass
                    await browser.close()
                    return {"keyword": keyword, "region": region, "error": "Could not find Google search box (Blocked or changed layout)"}

            # Press Enter to search
            await page.keyboard.press("Enter")
            await _random_delay(3.0, 5.0)

            # Wait for search results
            try:
                await page.wait_for_selector("#search", timeout=15000)
            except Exception:
                pass

            # Scroll down to find PAA section
            await _smooth_scroll(page, 400)
            await _random_delay(1.0, 2.0)

            # Recursive PAA expansion loop
            all_questions = []
            already_clicked = set()
            max_rounds = 8
            no_new_count = 0

            for round_num in range(max_rounds):
                logger.info(f"  Round {round_num + 1}: extracting questions...")

                # Check if page is still alive
                try:
                    await page.title()
                except Exception:
                    logger.warning("  Page closed unexpectedly, returning what we have.")
                    break

                current_questions = await _extract_paa_questions(page)
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
                    clicks = await _find_and_click_paa(page, already_clicked)
                except Exception as e:
                    logger.warning(f"  Click error: {e}")
                    clicks = 0

                if clicks == 0 and new_count == 0:
                    no_new_count += 1
                    if no_new_count >= 2:
                        logger.info(f"  No new questions found for 2 rounds, stopping.")
                        break
                    try:
                        await _smooth_scroll(page, random.randint(300, 600))
                        await _random_delay(1.5, 3.0)
                    except Exception:
                        break
                else:
                    no_new_count = 0

                await _random_delay(1.0, 2.0)

            try:
                await browser.close()
            except Exception:
                pass

            return {
                "keyword": keyword,
                "region": region,
                "questions": all_questions[:16],
                "count": min(len(all_questions), 16),
            }

    except asyncio.TimeoutError:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        return {"keyword": keyword, "region": region, "error": "Scraping timed out after 60 seconds"}
    except Exception as e:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        logger.error(f"Error scraping PAA for '{keyword}': {e}")
        return {"keyword": keyword, "region": region, "error": str(e)}


async def scrape_multiple(keywords: list[str], region: str = "us") -> list[dict]:
    """
    Scrape PAA questions for multiple keywords sequentially.
    Adds random delays between searches to appear human.
    """
    results = []
    for i, keyword in enumerate(keywords):
        keyword = keyword.strip()
        if not keyword:
            continue

        logger.info(f"Processing keyword {i + 1}/{len(keywords)}: '{keyword}'")

        max_retries = 2
        result = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                # If last error was a CAPTCHA, sleep longer
                wait_time = random.uniform(5.0, 10.0) if "CAPTCHA" in str(result.get("error", "")) else random.uniform(2.0, 5.0)
                logger.info(f"  Retry {attempt}/{max_retries} for '{keyword}' (Waiting {wait_time:.1f}s)...")
                await asyncio.sleep(wait_time)
                
            try:
                result = await asyncio.wait_for(
                    scrape_paa(keyword, region),
                    timeout=120, # Increased internal timeout
                )
            except asyncio.TimeoutError:
                result = {"keyword": keyword, "region": region, "error": "Timed out after 120 seconds"}
            except Exception as e:
                result = {"keyword": keyword, "region": region, "error": str(e)}

            # If we got at least 1 question, break out of retry loop
            if result and result.get("count", 0) > 0:
                break
                
            logger.warning(f"  Attempt {attempt + 1} failed for '{keyword}': {result.get('error', '0 questions found')}")

        results.append(result)

        if i < len(keywords) - 1:
            delay = random.uniform(3.0, 8.0)
            logger.info(f"  Waiting {delay:.1f}s before next keyword...")
            await asyncio.sleep(delay)

    return results
