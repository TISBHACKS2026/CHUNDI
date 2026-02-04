import requests
from bs4 import BeautifulSoup

# Allowed domains
ALLOWED_DOMAINS = [
    "britannica.com",
    "wikipedia.org",
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
    "britannica.com": "https://www.britannica.com/search?query={query}",
    "wikipedia.org": "https://en.wikipedia.org/w/index.php?search={query}&title=Special:Search&go=Go",
    "plato.stanford.edu": "https://plato.stanford.edu/entries/{query}/",
    "iep.utm.edu": "https://iep.utm.edu/{query}/",
    "ocw.mit.edu": "https://ocw.mit.edu/search/?q={query}",
    "openstax.org": "https://openstax.org/search?query={query}",
    "nap.edu": "https://www.nap.edu/search/?terms={query}",
    "arxiv.org": "https://export.arxiv.org/api/query?search_query=all:{query}",
    "nasa.gov": "https://www.nasa.gov/search?q={query}",
    "bbc.co.uk": "https://www.bbc.co.uk/search?q={query}"
}

def fetch_clean_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "edu-rag-bot/1.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.body
        text = main.get_text(" ", strip=True)
        return " ".join(text.split())
    except Exception:
        return ""

def browse_allowed_sources(query: str, max_pages_per_domain: int = 1) -> str:
    collected_text = []

    for domain in ALLOWED_DOMAINS:
        search_url_template = DOMAIN_SEARCH.get(domain)
        if not search_url_template:
            continue

        url = search_url_template.format(query=query.replace(" ", "+"))

        text = fetch_clean_text(url)
        if text:
            collected_text.append(text)

        if len(collected_text) >= max_pages_per_domain:
            break

    return "\n\n".join(collected_text)[:6000]
