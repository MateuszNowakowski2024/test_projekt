import os
from linkedin import LinkedIn
from dotenv import load_dotenv  # Only if using a .env file
import glob
import re

# Load variables from .env file if present
load_dotenv()

# Retrieve LinkedIn cookies from environment variables
cookies = {
    "JSESSIONID": os.getenv("LINKEDIN_JSESSIONID"),
    "li_at": os.getenv("LINKEDIN_LI_AT"),
    # Add any other required cookies if needed
}

# The URL to your blog (GitHub Pages URL or custom domain)
BLOG_URL = "http://127.0.0.1:8000/blog/ "

# Generate a short message. Fetch the title of the last generated post.
latest_post = None
files = glob.glob("docs/blog/posts/*.md")
if files:
    # Sort by modification time, get the newest file
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()
        # Attempt to extract title from the markdown
        title_match = re.search(r'^# (.+)', content, re.MULTILINE)
        if title_match:
            latest_post = title_match.group(1)
        else:
            latest_post = "New Post"

    # Create a short summary message
    message = f"Check out this week's new blog post: '{latest_post}'. Read it here: {BLOG_URL}"

    # Initialize LinkedIn client and post
    linkedin = LinkedIn(cookies=cookies)
    linkedin.post(message)
    print("Posted to LinkedIn successfully!")
else:
    print("No blog posts found. Nothing to share on LinkedIn.")
