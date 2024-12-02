import os
import json
from datetime import datetime
from googleapiclient.discovery import build
import yt_dlp
from config import (
    YOUTUBE_API_KEY,
    PLAYLIST_ID,
    PROCESSED_VIDEOS_FILE,
    TRANSCRIPTS_DIR
)

class YouTubeMonitor:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        self.processed_videos = self._load_processed_videos()
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'outtmpl': os.path.join(TRANSCRIPTS_DIR, '%(id)s.%(ext)s')
        }

    def _load_processed_videos(self):
        """Load the list of already processed videos."""
        if os.path.exists(PROCESSED_VIDEOS_FILE):
            with open(PROCESSED_VIDEOS_FILE, 'r') as f:
                return json.load(f)
        return []

    def _save_processed_videos(self):
        """Save the list of processed videos."""
        with open(PROCESSED_VIDEOS_FILE, 'w') as f:
            json.dump(self.processed_videos, f)

    def get_playlist_videos(self):
        """Get all videos from the configured playlist."""
        videos = []
        request = self.youtube.playlistItems().list(
            part="snippet",
            playlistId=PLAYLIST_ID,
            maxResults=50
        )

        while request:
            response = request.execute()
            
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                if video_id not in self.processed_videos:
                    videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'published_at': item['snippet']['publishedAt'],
                        'channel': item['snippet']['channelTitle']
                    })
            
            request = self.youtube.playlistItems().list_next(request, response)

        return videos

    def get_video_audio_url(self, video_url):
        """Download video audio and return the path to the audio file."""
        try:
            # Ensure transcripts directory exists
            os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info to get the ID
                info = ydl.extract_info(video_url, download=True)
                video_id = info['id']
                
                # Return the path to the downloaded audio file
                return os.path.join(TRANSCRIPTS_DIR, f'{video_id}.mp3')
                
        except Exception as e:
            raise Exception(f"Error downloading video {video_url}: {str(e)}")

    def mark_video_processed(self, video_id):
        """Mark a video as processed."""
        if video_id not in self.processed_videos:
            self.processed_videos.append(video_id)
            self._save_processed_videos()

    def get_new_videos(self):
        """Get all new videos that haven't been processed yet."""
        return self.get_playlist_videos()
