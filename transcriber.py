import os
import whisper
from openai import OpenAI
from datetime import datetime
import tiktoken
import logging
from config import (
    OPENAI_API_KEY,
    TRANSCRIPTS_DIR
)
from gdrive_handler import GoogleDriveHandler

class VideoTranscriber:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Only initialize Google Drive if credentials are configured
        self.gdrive = None
        if os.getenv('GOOGLE_DRIVE_CREDS_FILE'):
            self.gdrive = GoogleDriveHandler()
        
        # Create necessary directories if they don't exist
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    def count_tokens(self, text):
        """Count the number of tokens in a text."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text, max_tokens=4000):
        """Split text into chunks that fit within token limits."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        # Split into sentences (rough approximation)
        sentences = text.split('. ')
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_length + sentence_tokens > max_tokens:
                # Join the current chunk and add to chunks
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

    def transcribe_audio(self, audio_path):
        """Transcribe audio file using Whisper."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        if not os.path.getsize(audio_path) > 0:
            raise ValueError(f"Audio file is empty: {audio_path}")
            
        logging.info(f"Starting transcription of: {audio_path}")
        try:
            result = self.model.transcribe(audio_path)
            if not result or not result.get("text"):
                raise ValueError("Transcription produced no text")
            logging.info("Transcription completed successfully")
            return result["text"]
        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            raise

    def format_transcript_with_paragraphs(self, transcript):
        """Format transcript into paragraphs using OpenAI."""
        logging.info("Formatting transcript into paragraphs...")
        
        try:
            # Split transcript into smaller chunks
            chunks = self.chunk_text(transcript, max_tokens=4000)  # Reduced chunk size
            formatted_chunks = []
            
            for i, chunk in enumerate(chunks, 1):
                logging.info(f"Formatting chunk {i}/{len(chunks)}...")
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Format the text into clear paragraphs with double newlines between them."},
                            {"role": "user", "content": f"Format this text into paragraphs:\n\n{chunk}"}
                        ]
                    )
                    formatted_chunks.append(response.choices[0].message.content)
                except Exception as e:
                    logging.error(f"Error formatting chunk {i}, using original text: {str(e)}")
                    formatted_chunks.append(chunk)  # Use original text if formatting fails
            
            # Combine formatted chunks with proper spacing
            logging.info("Completed transcript formatting")
            return "\n\n".join(formatted_chunks)
            
        except Exception as e:
            logging.error(f"Error in formatting, using original text: {str(e)}")
            return transcript  # Return original text if formatting completely fails

    def generate_summary(self, transcript):
        """Generate a summary of the transcript using OpenAI."""
        logging.info("Generating summary...")
        
        try:
            chunks = self.chunk_text(transcript, max_tokens=4000)  # Reduced chunk size
            summaries = []
            
            for i, chunk in enumerate(chunks, 1):
                logging.info(f"Summarizing chunk {i}/{len(chunks)}...")
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Create a brief summary of the text."},
                            {"role": "user", "content": f"Summarize this text:\n\n{chunk}"}
                        ]
                    )
                    summaries.append(response.choices[0].message.content)
                except Exception as e:
                    logging.error(f"Error summarizing chunk {i}, skipping: {str(e)}")
            
            if len(summaries) > 1:
                try:
                    logging.info("Combining section summaries...")
                    combined_summary = "\n\n".join(summaries)
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Create a cohesive summary from these section summaries."},
                            {"role": "user", "content": f"Combine these summaries:\n\n{combined_summary}"}
                        ]
                    )
                    logging.info("Completed summary generation")
                    return response.choices[0].message.content
                except Exception as e:
                    logging.error(f"Error combining summaries, using concatenated version: {str(e)}")
                    return combined_summary
            
            logging.info("Completed summary generation")
            return summaries[0] if summaries else "Summary generation failed"
            
        except Exception as e:
            logging.error(f"Error in summary generation: {str(e)}")
            return "Summary generation failed"

    def create_transcript_doc(self, video_info, transcript):
        """Create a transcript file."""
        logging.info(f"Creating transcript document for: {video_info['title']}")
        
        try:
            # Format transcript with paragraphs
            formatted_transcript = self.format_transcript_with_paragraphs(transcript)
            
            # Generate summary
            summary = self.generate_summary(transcript)
            
            # Create final document content
            doc_content = f"""# {video_info['title']}

## Summary
{summary}

## Transcript
{formatted_transcript}
"""
            
            if self.gdrive:
                # Create Google Doc if Google Drive is configured
                doc_id = self.gdrive.create_doc(
                    video_info['title'],
                    doc_content,
                    video_info
                )
                logging.info(f"Created Google Doc with ID: {doc_id}")
                return doc_id
            else:
                # Save locally if Google Drive is not configured
                safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_path = os.path.join(TRANSCRIPTS_DIR, f"{safe_title}.md")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(doc_content)
                logging.info(f"Saved transcript to: {file_path}")
                return file_path
                
        except Exception as e:
            logging.error(f"Error creating transcript document: {str(e)}")
            # Save raw transcript as fallback
            safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_path = os.path.join(TRANSCRIPTS_DIR, f"{safe_title}_raw.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            logging.info(f"Saved raw transcript to: {file_path}")
            return file_path
