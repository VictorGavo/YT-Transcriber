# YouTube to Obsidian Transcription Bot

This bot monitors a YouTube playlist for new videos, transcribes them, and creates formatted notes in your Obsidian vault. It includes summaries and action items extracted from the video content.

## Features

- Monitors a specified YouTube playlist for new videos
- Transcribes video audio using OpenAI's Whisper
- Generates summaries and extracts action items using GPT-3.5
- Creates formatted Markdown notes in your Obsidian vault
- Tracks processed videos to avoid duplicates
- Includes comprehensive logging

## Prerequisites

- Python 3.8 or higher
- FFmpeg (see installation instructions below)
- YouTube Data API key
- OpenAI API key
- Obsidian vault directory

## Installation

1. Clone this repository

2. Install FFmpeg:
   - Download from https://github.com/BtbN/FFmpeg-Builds/releases
   - Download "ffmpeg-master-latest-win64-gpl.zip"
   - Extract the zip file
   - Copy the three executable files (ffmpeg.exe, ffplay.exe, ffprobe.exe) from the bin folder to a permanent location (e.g., C:\ffmpeg\bin)
   - Add that location to your system's PATH environment variable

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

## Configuration

Edit the `.env` file with your settings:

### YouTube API Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key to `YOUTUBE_API_KEY` in your `.env` file

### YouTube Playlist ID
1. Create or open a YouTube playlist you want to monitor
2. From the playlist URL (e.g., https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx)
3. Copy the ID after "list=" (PLxxxxxxxxxxxxxxx)
4. Set this as `PLAYLIST_ID` in your `.env` file
   - Note: The playlist must be either public or unlisted to be accessible

### OpenAI API Setup
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy it to `OPENAI_API_KEY` in your `.env` file

### Obsidian Configuration
Set `OBSIDIAN_VAULT_DIR` to the full path of your Obsidian vault directory

Example `.env` file:
```
YOUTUBE_API_KEY=your_youtube_api_key_here
PLAYLIST_ID=PLxxxxxxxxxxxxxxx
OPENAI_API_KEY=your_openai_api_key_here
OBSIDIAN_VAULT_DIR=C:/Users/YourUsername/Documents/ObsidianVault
```

## Usage

Run the bot:
```bash
python main.py
```

The bot will:
1. Check for new videos in the specified playlist
2. Download and transcribe any new videos
3. Generate summaries and highlights
4. Create formatted notes in your Obsidian vault
5. Log all activities to `youtube_monitor.log`

## Scheduling

### Windows Task Scheduler
1. Open Task Scheduler
2. Click "Create Basic Task"
3. Name it "YouTube Transcription Bot"
4. Select "Daily" or your preferred frequency
5. Set the start time and recurrence
6. Select "Start a program"
7. Program/script: `python`
8. Add arguments: `main.py`
9. Start in: `[Full path to your bot directory]`

### Linux/macOS Cron
1. Open terminal
2. Type `crontab -e`
3. Add a line for daily execution at e.g., 3 AM:
```bash
0 3 * * * cd /path/to/bot && /usr/bin/python3 main.py
```

### Using Multiple Playlists
To monitor different playlists:
1. Create a copy of the project directory
2. Update the `.env` file with the new playlist ID
3. Set up separate scheduling tasks for each instance

## Output Format

Each video creates a Markdown note with:
```markdown
---
Status: 
tags: input/videos
Links: 
Created: [ISO datetime]
Source: [video URL]
Author: [channel name]
Collection: YouTube
Finished: [ISO datetime]
Rating:
---
## Summary
[AI-generated summary]

## Notes
### Transcript
[Full video transcript]

## Highlights
[Key insights and memorable quotes]
```

## File Structure

- `main.py`: Main script orchestrating the process
- `youtube_monitor.py`: YouTube playlist monitoring and video handling
- `transcriber.py`: Audio transcription and note generation
- `config.py`: Configuration settings
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (create from template)

## Logging

The bot logs all activities to:
- Console output
- `youtube_monitor.log` file

## Error Handling

The bot includes comprehensive error handling and logging for:
- API failures
- Download issues
- Transcription problems
- File system errors

## Note

- Ensure your API keys have sufficient quota/credits
- The bot tracks processed videos to avoid duplicates
- Transcription quality depends on video audio quality
- The YouTube playlist must be public or unlisted
- Make sure to use the correct playlist ID format (PLxxxxxxxxxxxxxxx)

## Planned Improvements

1. Performance Optimization
- Consider caching API responses to reduce OpenAI API calls
- Implement parallel processing for multiple videos
- Add batch processing capabilities for efficiency
2. Robustness
- Add retry mechanisms for API calls
- Implement rate limiting for API requests
- Add validation for Google Drive path accessibility
- Consider backup locations if Google Drive is unavailable
3. Features
- Add support for multiple playlist monitoring
- Implement content tagging based on video topics
- Add progress tracking for long transcriptions
- Consider implementing a simple GUI
4. Code Quality
- Add type hints for better code maintainability
- Implement more unit tests
- Add input validation for video URLs
- Consider using dataclasses for video information
5. Documentation
- Add docstring type hints
- Include more code comments for complex logic
- Create developer documentation
- Add setup instructions for Google Drive integration
6. Monitoring & Maintenance
- Add system resource monitoring
- Implement automated error reporting
- Add periodic cleanup of temporary files
- Consider adding health checks for dependencies
