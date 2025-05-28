import os

from robocorp.browser import browser
from sema4ai.actions import Response, action

HEADLESS_BROWSER = True


@action
def get_wikipedia_article_summary(article_url: str) -> Response[str]:
    """Get the summary of a Wikipedia article.

    Args:
        article_url: The URL of the Wikipedia article to get the summary of.

    Returns:
        A string containing the summary of the Wikipedia article.
    """
    browser.configure(browser_engine="chromium", headless=HEADLESS_BROWSER)

    page = browser.goto(article_url)

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_load_state("networkidle")

    inexistent_function_call()

    paragraphs = page.query_selector_all(".mw-content-ltr>p:not(.mw-empty-elt)")
    summary = paragraphs[0].inner_text()

    print(summary)

    return Response(result=summary)
