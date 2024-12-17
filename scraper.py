import requests
from bs4 import BeautifulSoup
import re
import feedparser
from feedparser import FeedParserDict



class Scraper:
    def __init__(self, url, character_limit=2000):
        self.url: str = url
        self.character_limit = character_limit

    def fetch_content(self):
        try:
            if self.url.endswith('rss') or self.url.endswith('xml') or 'feed' in self.url:
                return self.rss_parse(self.url)
            response = requests.get(self.url)
            response.raise_for_status()
            return self.parse(response.text)
        except Exception as e:
            print(f"Error fetching content from {self.url}: {e}")
            return None

    def parse(self, content):
        soup = BeautifulSoup(content, 'html.parser')

        # Removing undesired elements
        for element in soup.find_all(["nav", "header"]):
            element.decompose()

        # Removing script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Extract text using the get_text() method
        all_text = soup.get_text()

        # Clean up the text
        lines = (line.strip() for line in all_text.splitlines())
        all_text_clean = re.sub(r'\s+', ' ', (' '.join(line for line in lines if line)))

        return all_text_clean[0:self.character_limit]

    def rss_parse(self, url):
        feed: FeedParserDict = feedparser.parse(url)
        if not feed.entries:
            return None
        # Instead of random entry, we might gather a few entries
        entries_summaries = []
        for entry in feed.entries[:3]:  # take top 3 entries
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            # Combine title and summary for context
            combined = f"Title: {title}\nSummary: {summary}\nLink: {link}\n"
            entries_summaries.append(combined)
        return "\n".join(entries_summaries)