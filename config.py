import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# YouTube API Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
PLAYLIST_ID = os.getenv('PLAYLIST_ID')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# File Paths
TRANSCRIPTS_DIR = 'transcripts'
OBSIDIAN_VAULT_DIR = os.getenv('OBSIDIAN_VAULT_DIR', 'obsidian_vault')
GOOGLE_DRIVE_DIR = r"G:\My Drive\Projects\Deep Learn\Unread"
PROCESSED_VIDEOS_FILE = 'processed_videos.json'

# Markdown Template
MARKDOWN_TEMPLATE = """---
Status: 
tags: input/videos
Links: 
Created: {date}
Source: {url}
Author: {channel}
Collection: YouTube
Finished: {date}
Rating:
---
## Summary
{summary}

## Notes
### Transcript

{transcript}

## Highlights
{action_items}
"""
