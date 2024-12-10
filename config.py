import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# YouTube API Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
PLAYLIST_ID = os.getenv('PLAYLIST_ID')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Drive Configuration
GOOGLE_DRIVE_CREDS_FILE = os.getenv('GOOGLE_DRIVE_CREDS_FILE')
GDRIVE_UNREAD_FOLDER_ID = os.getenv('GDRIVE_UNREAD_FOLDER_ID')  # Folder for new transcripts
GDRIVE_PROCESSED_FOLDER_ID = os.getenv('GDRIVE_PROCESSED_FOLDER_ID')  # Folder for processed docs
OBSIDIAN_VAULT_PATH = os.getenv('OBSIDIAN_VAULT_PATH')  # Path to Obsidian vault

# File Paths
TRANSCRIPTS_DIR = 'transcripts'
PROCESSED_VIDEOS_FILE = 'processed_videos.json'

# Markdown Templates
GDRIVE_DOC_TEMPLATE = """
{transcript}
"""

OBSIDIAN_NOTE_TEMPLATE = """---
Status: Processed
tags: input/videos
Links: 
Created: {created_date}
Source: {url}
Author: {channel}
Collection: YouTube
Processed: {processed_date}
Rating:
---

## Highlights and Comments
{highlights}

## Summary
{summary}

## Notes
### Transcript
{transcript}
"""
