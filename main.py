import os
import time
import logging
from youtube_monitor import YouTubeMonitor
from transcriber import VideoTranscriber
from gdrive_handler import GoogleDriveHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_monitor.log'),
        logging.StreamHandler()
    ]
)

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

def main():
    youtube_monitor = YouTubeMonitor()
    transcriber = VideoTranscriber()
    gdrive = GoogleDriveHandler()
    
    logging.info("Starting YouTube transcription bot...")
    
    while True:
        try:
            # Check for new videos
            new_videos = youtube_monitor.get_new_videos()
            
            for video in new_videos:
                logging.info(f"Processing new video: {video['title']}")
                process_video(video, youtube_monitor, transcriber)
            
            # Check Google Drive for processed files
            gdrive.monitor_drive()
            
            # Wait before next check
            time.sleep(300)  # 5 minutes
            
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()
