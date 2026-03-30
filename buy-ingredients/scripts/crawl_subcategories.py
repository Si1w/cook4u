"""Crawl M&S category pages to find sub-category pills."""

import re
import time
from playwright.sync_api import sync_playwright

CATALOGUE_PATH = "../references/marksandspencer/food-catalogue.md"
BASE_URL = "https://www.marksandspencer.com/food/l/"


def slugify(name: str) -> str:
    """Convert category name to URL slug."""
    s = name.strip()
    s = s.replace("&", "and")
    s = s.replace("'", "")
    s = s.replace(",", "")
    s = re.sub(r"\s+", "-", s)
    return s.lower()


def parse_catalogue(path: str) -> list[tuple[str, list[str]]]:
    """Parse food-catalogue.md, return leaf nodes with their full slug paths.

    Only processes categories under '## Common Categories for Cooking'.
    Returns list of (display_path, slug_parts) for each leaf node.
    """
    with open(path) as f:
        lines = f.readlines()

    in_section = False
    nodes = []  # list of (indent_level, name, slug)
    current_h3 = None

    for i, line in enumerate(lines):
        stripped = line.rstrip()

        if stripped == "## Common Categories for Cooking":
            in_section = True
            continue
        if stripped.startswith("## ") and in_section:
            break  # reached next section
        if not in_section:
            continue

        # H3 = top-level category
        if stripped.startswith("### "):
            current_h3 = stripped[4:].strip()
            nodes.append((0, current_h3, slugify(current_h3)))
            continue

        # List items
        match = re.match(r"^(\s*)- (.+)$", stripped)
        if match and current_h3:
            indent = len(match.group(1))
            name = match.group(2).strip()
            level = indent // 2 + 1  # 0-indent = level 1, 2-indent = level 2, etc.
            nodes.append((level, name, slugify(name)))

    # Find leaf nodes (nodes with no deeper child following them)
    leaves = []
    for i, (level, name, slug) in enumerate(nodes):
        # Check if next node is a child (deeper level)
        is_leaf = True
        if i + 1 < len(nodes):
            next_level = nodes[i + 1][0]
            if next_level > level:
                is_leaf = False

        if is_leaf:
            # Build full path from ancestors
            path_parts = []
            target_level = level
            # Walk backwards to find all ancestors
            for j in range(i, -1, -1):
                if nodes[j][0] < target_level:
                    path_parts.insert(0, nodes[j][2])
                    target_level = nodes[j][0]
                    if target_level == 0:
                        break
                elif nodes[j][0] == level and j == i:
                    path_parts.append(nodes[j][2])

            leaves.append(("/".join(path_parts), name))

    return leaves


def crawl_subcategories(leaves: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Visit each leaf page and extract sub-category pills."""
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="en-GB")

        # Accept cookies once
        page.goto(BASE_URL + leaves[0][0], wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
            btn = page.locator("button:has-text('Accept All Cookies')")
            if btn.is_visible(timeout=3000):
                btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

        for path, name in leaves:
            url = BASE_URL + path
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)

                # Find pill links with browse-by-aisle intid
                pills = page.locator("a[href*='browse-by-aisle']").all()
                subcats = []
                for pill in pills:
                    text = pill.inner_text().strip()
                    if text:
                        subcats.append(text)

                if subcats:
                    results[path] = subcats
                    print(f"  {name} ({path}) -> {subcats}")
                else:
                    print(f"  {name} ({path}) -> (no subcategories)")
            except Exception as e:
                print(f"  {name} ({path}) -> ERROR: {e}")

        browser.close()

    return results


if __name__ == "__main__":
    print("Parsing catalogue...")
    leaves = parse_catalogue(CATALOGUE_PATH)
    print(f"Found {len(leaves)} leaf categories to check.\n")

    for path, name in leaves:
        print(f"  {path} ({name})")

    print("\nCrawling M&S pages...\n")
    results = crawl_subcategories(leaves)

    print(f"\n=== SUMMARY ===")
    print(f"Categories with sub-categories: {len(results)}")
    for path, subcats in sorted(results.items()):
        print(f"  {path}: {', '.join(subcats)}")