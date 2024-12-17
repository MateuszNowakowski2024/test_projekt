import openai
import os
from llm import tutorial_post
from utils import get_recent_posts_titles, extract_title_and_insert_excerpt, save_post

openai.api_key = os.getenv("OPENAI_API_KEY")


if __name__ == "__main__":
    recent_titles = get_recent_posts_titles()
    post = tutorial_post(recent_titles)
    title, final_content = extract_title_and_insert_excerpt(post)
    save_post(final_content, title)
