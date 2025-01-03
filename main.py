import os
import sys
import time
import signal
import logging
from logging.handlers import RotatingFileHandler
from youtube_monitor import YouTubeMonitor
from transcriber import VideoTranscriber
from gdrive_handler import GoogleDriveHandler
from config import GOOGLE_DRIVE_CREDS_FILE

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
        logging.StreamHandler(sys.stdout)  # Ensure output goes to stdout
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
        logging.info(f"Starting to process video: {video_info['title']}")
        
        # Download audio
        logging.info("Downloading audio...")
        try:
            audio_path = youtube_monitor.get_video_audio_url(video_info['url'])
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found at {audio_path}")
            logging.info(f"Successfully downloaded audio to: {audio_path}")
        except Exception as e:
            logging.error(f"Failed to download audio: {str(e)}")
            return False
        
        # Transcribe audio
        logging.info("Transcribing audio...")
        try:
            transcript = transcriber.transcribe_audio(audio_path)
            logging.info("Successfully transcribed audio")
        except Exception as e:
            logging.error(f"Failed to transcribe audio: {str(e)}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return False
        
        # Create transcript document
        logging.info("Creating transcript document...")
        try:
            doc_id = transcriber.create_transcript_doc(video_info, transcript)
            logging.info(f"Successfully created transcript document: {doc_id}")
        except Exception as e:
            logging.error(f"Failed to create transcript document: {str(e)}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return False
        
        # Mark video as processed
        youtube_monitor.mark_video_processed(video_info['id'])
        
        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logging.info("Cleaned up audio file")
            
        logging.info(f"Successfully processed video: {video_info['title']}")
        return True
        
    except Exception as e:
        logging.error(f"Error processing video {video_info['title']}: {str(e)}")
        return False

def check_system_resources():
    """Check system resources and log warnings if necessary."""
    try:
        # Check disk space using shutil
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_space_gb = free / (1024**3)
        if free_space_gb < 1.0:  # Less than 1GB free
            logging.warning(f"Low disk space: {free_space_gb:.2f}GB remaining")
        else:
            logging.info(f"Available disk space: {free_space_gb:.2f}GB")
        
    except Exception as e:
        logging.error(f"Error checking system resources: {str(e)}")

def main():
    logging.info("Starting YouTube transcription bot...")
    
    youtube_monitor = YouTubeMonitor()
    transcriber = VideoTranscriber()
    
    # Only initialize Google Drive if credentials are configured
    gdrive = None
    if GOOGLE_DRIVE_CREDS_FILE:
        gdrive = GoogleDriveHandler()
        logging.info("Google Drive integration enabled")
    else:
        logging.info("Google Drive integration disabled - transcripts will be saved locally")
    
    retry_delay = 60
    max_delay = 3600  # 1 hour
    
    while not should_exit:
        try:
            # Check system resources
            check_system_resources()
            
            # Check for new videos
            logging.info("Checking for new videos...")
            new_videos = youtube_monitor.get_new_videos()
            
            if not new_videos:
                logging.info("No new videos found")
            else:
                logging.info(f"Found {len(new_videos)} new videos")
            
            for video in new_videos:
                if should_exit:
                    break
                    
                logging.info(f"Processing video: {video['title']}")
                success = process_video(video, youtube_monitor, transcriber)
                if not success:
                    logging.warning(f"Failed to process video: {video['title']}, will retry on next run")
            
            # Check Google Drive for processed files if enabled
            if gdrive:
                logging.info("Checking Google Drive for processed files...")
                gdrive.monitor_drive()
            
            # Reset retry delay on successful iteration
            retry_delay = 60
            
            # Wait before next check
            logging.info("Waiting 5 minutes before next check...")
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
