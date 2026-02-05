import requests
from bs4 import BeautifulSoup

ALLOWED_DOMAINS = [
    "wikipedia.org",
    "britannica.com",
    "plato.stanford.edu",
    "iep.utm.edu",
    "ocw.mit.edu",
    "openstax.org",
    "nap.edu",
    "arxiv.org",
    "nasa.gov",
    "bbc.co.uk"
]

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
    forced_domain: str | None = None,
    max_pages_per_domain: int = 1
) -> str:
    collected = []

    domains = [forced_domain] if forced_domain else ALLOWED_DOMAINS

    for domain in domains:
        if domain not in DOMAIN_SEARCH:
            continue

        search_url = DOMAIN_SEARCH[domain].format(
            query=query.replace(" ", "+")
        )

        text = fetch_clean_text(search_url)
        if text:
            collected.append(f"[SOURCE: {domain}]\n{text[:3000]}")

        if len(collected) >= max_pages_per_domain:
            break

    return "\n\n".join(collected)
