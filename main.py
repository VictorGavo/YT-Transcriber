import os
import sys
import time
import signal
import logging
from logging.handlers import RotatingFileHandler
from youtube_monitor import YouTubeMonitor
from transcriber import VideoTranscriber
from gdrive_handler import GoogleDriveHandler

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'youtube_monitor.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Global flag for graceful shutdown
should_exit = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global should_exit
    logging.info("Received shutdown signal, cleaning up...")
    should_exit = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def process_video(video_info, youtube_monitor, transcriber):
    """Process a single video."""
    try:
        # Download audio
        audio_path = youtube_monitor.get_video_audio_url(video_info['url'])
        
        # Transcribe audio
        transcript = transcriber.transcribe_audio(audio_path)
        
        # Create Google Doc
        doc_id = transcriber.create_transcript_doc(video_info, transcript)
        
        # Mark video as processed
        youtube_monitor.mark_video_processed(video_info['id'])
        
        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        logging.info(f"Successfully processed video: {video_info['title']}")
        
    except Exception as e:
        logging.error(f"Error processing video {video_info['title']}: {str(e)}")
        return False
        
    return True

def check_system_resources():
    """Check system resources and log warnings if necessary."""
    try:
        # Check disk space
        disk = os.statvfs('.')
        free_space_gb = (disk.f_bavail * disk.f_frsize) / (1024**3)
        if free_space_gb < 1.0:  # Less than 1GB free
            logging.warning(f"Low disk space: {free_space_gb:.2f}GB remaining")
        
        # Add more resource checks as needed
        
    except Exception as e:
        logging.error(f"Error checking system resources: {str(e)}")

def main():
    youtube_monitor = YouTubeMonitor()
    transcriber = VideoTranscriber()
    gdrive = GoogleDriveHandler()
    
    logging.info("Starting YouTube transcription bot...")
    
    retry_delay = 60
    max_delay = 3600  # 1 hour
    
    while not should_exit:
        try:
            # Check system resources
            check_system_resources()
            
            # Check for new videos
            new_videos = youtube_monitor.get_new_videos()
            
            for video in new_videos:
                if should_exit:
                    break
                    
                logging.info(f"Processing new video: {video['title']}")
                process_video(video, youtube_monitor, transcriber)
            
            # Check Google Drive for processed files
            gdrive.monitor_drive()
            
            # Reset retry delay on successful iteration
            retry_delay = 60
            
            # Wait before next check
            for _ in range(30):  # Break up 5-minute sleep into 10-second intervals
                if should_exit:
                    break
                time.sleep(10)
            
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(min(retry_delay, max_delay))
            retry_delay *= 2  # Exponential backoff
    
    logging.info("Shutting down YouTube transcription bot...")
    sys.exit(0)

if __name__ == "__main__":
    main()
