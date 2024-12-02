import os
import logging
from youtube_monitor import YouTubeMonitor
from transcriber import VideoTranscriber
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_monitor.log'),
        logging.StreamHandler()
    ]
)

class YouTubeTranscriptionBot:
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
        self.transcriber = VideoTranscriber()

    def process_video(self, video_info, current_num, total_num):
        """Process a single video: download, transcribe, and create Obsidian note."""
        start_time = datetime.now()
        logging.info(f"[{current_num}/{total_num}] Processing video: {video_info['title']}")
        print(f"\n[{current_num}/{total_num}] Processing: {video_info['title']}")
        
        try:
            # Download audio and get the file path
            print("Downloading audio...")
            audio_path = self.youtube_monitor.get_video_audio_url(video_info['url'])
            if not audio_path or not os.path.exists(audio_path):
                logging.error(f"Could not download audio for video: {video_info['url']}")
                return False

            # Transcribe audio
            transcript = self.transcriber.transcribe_audio(audio_path)
            
            # Create Obsidian note
            note_path = self.transcriber.create_obsidian_note(video_info, transcript)
            
            # Calculate processing time
            processing_time = datetime.now() - start_time
            logging.info(f"Successfully created note at: {note_path}")
            print(f"✓ Successfully processed in {processing_time.total_seconds():.1f} seconds")
            
            # Mark video as processed
            self.youtube_monitor.mark_video_processed(video_info['id'])
            
            # Clean up the audio file
            try:
                os.remove(audio_path)
                logging.info(f"Cleaned up audio file: {audio_path}")
            except Exception as e:
                logging.warning(f"Could not delete audio file {audio_path}: {str(e)}")
            
            return True

        except Exception as e:
            logging.error(f"Error processing video {video_info['url']}: {str(e)}")
            print(f"✗ Error: {str(e)}")
            return False

    def run(self):
        """Main execution loop."""
        logging.info("Starting YouTube Transcription Bot")
        print("\nStarting YouTube Transcription Bot")
        
        try:
            # Get new videos from playlist
            new_videos = self.youtube_monitor.get_new_videos()
            
            if not new_videos:
                logging.info("No new videos found")
                print("No new videos found")
                return
            
            total_videos = len(new_videos)
            logging.info(f"Found {total_videos} new videos")
            print(f"Found {total_videos} new videos to process")
            
            # Process each video
            for i, video in enumerate(new_videos, 1):
                try:
                    self.process_video(video, i, total_videos)
                except KeyboardInterrupt:
                    print("\n\nProcessing interrupted by user. Progress has been saved.")
                    logging.info("Processing interrupted by user")
                    break
                except Exception as e:
                    logging.error(f"Error processing video {video['url']}: {str(e)}")
                    print(f"✗ Error processing video: {str(e)}")
                    continue
                
        except Exception as e:
            logging.error(f"Error in main execution: {str(e)}")
            print(f"Error: {str(e)}")
        
        print("\nProcessing complete!")

if __name__ == "__main__":
    try:
        bot = YouTubeTranscriptionBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\nBot stopped by user. Progress has been saved.")
        logging.info("Bot stopped by user")
