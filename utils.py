from datetime import datetime
from enum import Enum
import mimetypes
import os
import json
from os import path
import glob
import re
import yaml

class MEDIA_CATEGORY(Enum):
    IMAGE = 1,
    # OTHERS


def custom_print(message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")


def get_content_type(file_path):
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type


def get_file_data (fname, protocol="r", incl_meta=False):
    # Load websites from the JSON file
    with open(fname, protocol) as file:
        data = None
        if "json" in str.lower(fname):
            data = json.load(file)
        else:
            data = file.read().strip()
        return ( data, path.getsize(fname), get_content_type(fname) ) if incl_meta else data
    
def extract_post_content():
    """Extract the latest post title and content from your markdown files."""
    files = glob.glob("docs/blog/posts/*.md")
    if not files:
        return None, None

    # Sort by modification time, get the newest file
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Attempt to extract title
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    if title_match:
        latest_post = title_match.group(1)
    else:
        latest_post = "New Post"

    # Extract content after the title
    lines = content.split("\n")
    title_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            title_index = i
            break

    post_body_lines = lines[title_index+1:] if title_index is not None else lines
    post_body_lines = [l.strip() for l in post_body_lines if l.strip()]

    content_blocks = []
    current_block = []
    for line in post_body_lines:
        if line == "":
            if current_block:
                content_blocks.append(" ".join(current_block))
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        content_blocks.append(" ".join(current_block))

    # Take the first two blocks as a summary
    summary_blocks = content_blocks[:2]
    summary_text = "\n\n".join(summary_blocks).strip()

    return latest_post, summary_text

def get_recent_posts_titles(directory="docs/blog/posts", limit=3):
    """
    Retrieve titles of recent posts by reading from existing markdown files.
    Assumes that the title is in the YAML front matter or the first heading (# Title).
    """
    posts = sorted(glob.glob(os.path.join(directory, "*.md")), key=os.path.getmtime, reverse=True)
    recent_titles = []
    for post in posts[:limit]:
        with open(post, "r", encoding="utf-8") as f:
            content = f.read()
            # Try to extract title from front matter or first heading
            front_matter_match = re.search(r"(?m)^title:\s*(.*)", content)
            if front_matter_match:
                title = front_matter_match.group(1).strip('"\' ')
            else:
                heading_match = re.search(r"(?m)^#\s+(.*)", content)
                title = heading_match.group(1).strip() if heading_match else os.path.basename(post)
            recent_titles.append(title)
    return recent_titles



def extract_title_and_insert_excerpt(content):
    """
    Extracts the title from the content and inserts an excerpt marker (`<!-- more -->`).
    """
    lines = content.split("\n")
    title_line = next((l for l in lines if l.startswith("# ")), "# Recent AI Advancements")
    title = title_line.replace("# ", "").strip()
    
    if "<!-- more -->" in content:
        return title, content
    
    try:
        title_index = lines.index(title_line)
        paragraph_lines = 0
        first_paragraph_end = title_index + 1
        
        for i in range(title_index + 1, len(lines)):
            line = lines[i].strip()
            if line == "":
                first_paragraph_end = i
                break
            paragraph_lines += 1
            first_paragraph_end = i + 1

        if paragraph_lines >= 5:
            insert_position = first_paragraph_end
        else:
            insert_position = title_index + 1 + 5
            insert_position = min(insert_position, len(lines))
        
        lines.insert(insert_position, "<!-- more -->")
        
    except Exception as e:
        print(f"Error inserting excerpt: {e}")
        insert_position = title_index + 1
        lines.insert(insert_position, "<!-- more -->")
    
    modified_content = "\n".join(lines)
    return title, modified_content

def save_post(content, title):
    # Create a slug from the title
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    
    metadata = {
        'title': title,
        'date': datetime.now().date()
    }

    md = f"---\n{yaml.dump(metadata)}---\n\n{content}"
    file_path = f"docs/blog/posts/{slug}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Generated blog post: {file_path}")

