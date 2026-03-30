"""Search M&S website for ingredients and check store availability."""

import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

MS_SEARCH_URL = (
    "https://www.marksandspencer.com/food/l/"
    "{path}?searchRedirect={query}"
)
MAX_RESULTS_PER_ITEM = 5
STATE_FILE = Path(__file__).parent / "../.cookie/ms-state.json"


def accept_cookies(page):
    """Dismiss cookie consent banner if present."""
    try:
        btn = page.locator("button:has-text('Accept All Cookies')")
        if btn.is_visible(timeout=3000):
            btn.click()
    except Exception:
        pass


def select_store(page, postcode: str):
    """Select the nearest M&S store by postcode so prices are shown."""
    store_btn = page.locator("button:has-text('Select your store')")
    if not store_btn.is_visible(timeout=5000):
        return
    store_btn.click()
    page.wait_for_timeout(2000)

    search_input = page.locator("#searchTextInput")
    search_input.type(postcode, delay=100)
    page.wait_for_timeout(500)
    search_input.press("Enter")
    page.wait_for_timeout(5000)

    # First store is auto-selected; click "Select Store" to confirm
    confirm_btn = page.locator("button:text-is('Select Store')")
    if confirm_btn.is_visible(timeout=5000):
        confirm_btn.click()
        page.wait_for_timeout(5000)


def parse_query_item(item: str) -> tuple[str, str]:
    """Parse 'path:query' into (path, query).

    Example: 'fruit-and-vegetables/fresh-vegetables/root-vegetables/carrots:carrot'
    """
    path, _, query = item.partition(":")
    return path.strip(), query.strip()


def search_ingredient(page, query: str, path: str) -> list[dict]:
    """Search M&S for a single ingredient, return top results."""
    url = MS_SEARCH_URL.format(path=path, query=query.replace(" ", "+"))
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    accept_cookies(page)

    results = []
    cards = page.locator(".product-card_rootBox__BcM9P").all()

    for card in cards:
        if len(results) >= MAX_RESULTS_PER_ITEM:
            break
        try:
            name_el = card.locator("h3")
            if not name_el.is_visible(timeout=500):
                continue
            name = name_el.inner_text().strip()
            if not name:
                continue

            # Parse full card text for price and stock
            text = card.inner_text()
            price = ""
            stock = ""
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("£"):
                    price = line
                elif line in ("In stock", "Out of stock"):
                    stock = line

            results.append({"name": name, "price": price, "stock": stock})
        except Exception:
            continue

    return results


def main():
    parser = argparse.ArgumentParser(description="Search M&S for ingredients")
    parser.add_argument("--postcode", default=None, help="UK postcode for store lookup (optional)")
    parser.add_argument(
        "--query", required=True,
        help="Comma-separated items in 'path:ingredient' format, "
             "e.g. 'fruit-and-vegetables/fresh-vegetables/root-vegetables/carrots:carrot'",
    )
    args = parser.parse_args()

    items = [q.strip() for q in args.query.split(",") if q.strip()]
    all_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Restore saved cookies if available
        if STATE_FILE.exists():
            context = browser.new_context(locale="en-GB", storage_state=str(STATE_FILE))
        else:
            context = browser.new_context(locale="en-GB")

        page = context.new_page()

        # Select store if postcode provided and no store set yet
        if args.postcode:
            page.goto(MS_SEARCH_URL.format(path=parse_query_item(items[0])[0], query=parse_query_item(items[0])[1].replace(" ", "+")), wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            accept_cookies(page)
            if page.locator("button:has-text('Select your store')").is_visible(timeout=3000):
                select_store(page, args.postcode)
                context.storage_state(path=str(STATE_FILE))

        for item in items:
            path, ingredient = parse_query_item(item)
            products = search_ingredient(page, ingredient, path)
            all_results[ingredient] = products

        browser.close()

    print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()