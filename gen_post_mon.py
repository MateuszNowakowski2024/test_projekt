import openai
import os
from scraper import Scraper
from llm import blog_post
from utils import get_recent_posts_titles, extract_title_and_insert_excerpt, save_post

openai.api_key = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":
    # Example feeds or websites:
    urls = [
        "https://www.kdnuggets.com/feed",    
        "https://dataconomy.com/",  
        "https://aibusiness.com/rss.xml"   
    ]

    # Scrape from multiple sources and combine
    scraped_contents = []
    for u in urls:
        scraper = Scraper(u)
        content = scraper.fetch_content()
        if content:
            scraped_contents.append(content)

    combined_scraped_context = "\n\n".join(scraped_contents)

    recent_titles = get_recent_posts_titles()
    post = blog_post(recent_titles, combined_scraped_context)
    title, final_content = extract_title_and_insert_excerpt(post)
    save_post(final_content, title)
