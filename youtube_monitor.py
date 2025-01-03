import os
import json
from datetime import datetime
import time
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
        
        # Configure yt-dlp options with minimal settings
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(TRANSCRIPTS_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'no_check_certificate': True,
            'ignoreerrors': True,
            'no_color': True,
            'noprogress': True,
            'noplaylist': True,
            'prefer_ffmpeg': True,
            'hls_prefer_native': True,
            'cachedir': False,
            'rm_cachedir': True
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

    def get_video_audio_url(self, video_url, max_retries=3):
        """Download video audio and return the path to the audio file."""
        # Ensure transcripts directory exists
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        
        # Extract video ID from URL
        video_id = video_url.split('v=')[1]
        audio_path = os.path.join(TRANSCRIPTS_DIR, f'{video_id}.mp3')
        
        # If file already exists, return it
        if os.path.exists(audio_path):
            return audio_path
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Download the audio
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    print(f"Downloading audio for video: {video_url}")
                    ydl.download([video_url])
                
                # Verify the file was created
                if os.path.exists(audio_path):
                    print(f"Successfully downloaded audio to: {audio_path}")
                    return audio_path
                else:
                    raise Exception("Download completed but file not found")
                    
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                # Wait between retries with exponential backoff
                wait_time = 5 * (2 ** (retry_count - 1))
                print(f"Error occurred. Waiting {wait_time} seconds before retry {retry_count}/{max_retries}")
                print(f"Error details: {last_error}")
                time.sleep(wait_time)
        
        raise Exception(f"Error downloading video {video_url} after {max_retries} retries: {last_error}")

    def mark_video_processed(self, video_id):
        """Mark a video as processed."""
        if video_id not in self.processed_videos:
            self.processed_videos.append(video_id)
            self._save_processed_videos()

    def get_new_videos(self):
        """Get all new videos that haven't been processed yet."""
        return self.get_playlist_videos()
