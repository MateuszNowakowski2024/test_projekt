import os
from dotenv import load_dotenv
import openai
from llm import generate_intro_thu
from linkedin import LinkedIn
from linkedin import login_linkedin
from utils import extract_post_content

load_dotenv()

# Your LinkedIn credentials from environment or secure storage
USERNAME = os.getenv("LINKEDIN_USERNAME")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Your blog URL
BLOG_URL = "http://127.0.0.1:8000/blog/"


def main():
    # 1. Log in to LinkedIn and get a session
    session = login_linkedin(USERNAME, PASSWORD)

    # Extract cookies from the logged-in session
    li_at = session.cookies.get('li_at')
    jsessionid = session.cookies.get('JSESSIONID')

    # 2. Extract the blog post content and prepare the LinkedIn message
    latest_post, summary_text = extract_post_content()
    if not latest_post:
        print("No blog posts found. Nothing to share on LinkedIn.")
        return

    # Generate a dynamic introduction using the LLM
    message = generate_intro_thu(latest_post, summary_text, BLOG_URL)

    # 3. Initialize LinkedIn client and post
    linkedin = LinkedIn(cookies={"li_at": li_at, "JSESSIONID": jsessionid})
    linkedin.post(message)
    print("Posted to LinkedIn successfully!")


if __name__ == "__main__":
    main()
