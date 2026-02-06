import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

DOMAIN_SEARCH = {
    "wikipedia.org": "https://en.wikipedia.org/w/index.php?search={query}",
    "britannica.com": "https://www.britannica.com/search?query={query}",
    "plato.stanford.edu": "https://plato.stanford.edu/search/searcher.py?query={query}",
    "iep.utm.edu": "https://iep.utm.edu/?s={query}",
    "ocw.mit.edu": "https://ocw.mit.edu/search/?q={query}",
    "openstax.org": "https://openstax.org/search?query={query}",
    "nap.edu": "https://www.nap.edu/search/?terms={query}",
    "arxiv.org": "https://export.arxiv.org/api/query?search_query=all:{query}",
    "nasa.gov": "https://www.nasa.gov/search?q={query}",
    "bbc.co.uk": "https://www.bbc.co.uk/search?q={query}"
}


def fetch_clean_text(url: str) -> str:
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "edu-rag-bot/1.0"}
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.body
        if not main:
            return ""

        text = main.get_text(" ", strip=True)
        return " ".join(text.split())

    except Exception:
        return ""


def browse_allowed_sources(
    query: str,
    forced_domain: str,
    max_pages: int = 1
) -> str:
    if forced_domain not in DOMAIN_SEARCH:
        return ""

    search_url = DOMAIN_SEARCH[forced_domain].format(
        query=quote_plus(query)
    )

    text = fetch_clean_text(search_url)

    if not text:
        return ""

    return f"[SOURCE: {forced_domain}]\n{text[:3000]}"
