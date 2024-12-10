import os
import whisper
from openai import OpenAI
from datetime import datetime
import tiktoken
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
        self.gdrive = GoogleDriveHandler()
        
        # Create necessary directories if they don't exist
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    def count_tokens(self, text):
        """Count the number of tokens in a text."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text, max_tokens=12000):
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
        print(f"Transcribing audio file: {audio_path}")
        result = self.model.transcribe(audio_path)
        return result["text"]

    def format_transcript_with_paragraphs(self, transcript):
        """Format transcript into paragraphs using OpenAI."""
        print("Formatting transcript into paragraphs...")
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that formats text into clear, readable paragraphs. Format the text with proper paragraph breaks by adding two newlines (\\n\\n) between paragraphs. Each paragraph should be a cohesive group of related sentences. Keep the original content intact but make it more readable with appropriate paragraph structure."},
                {"role": "user", "content": f"Please format this transcript into clear paragraphs with proper spacing (double newlines between paragraphs):\n\n{transcript}"}
            ]
        )
        return response.choices[0].message.content

    def generate_summary(self, transcript):
        """Generate a summary of the transcript using OpenAI."""
        print("Generating summary...")
        
        chunks = self.chunk_text(transcript)
        summaries = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries of video transcripts."},
                    {"role": "user", "content": f"Please provide a concise summary of the following transcript section:\n\n{chunk}"}
                ]
            )
            summaries.append(response.choices[0].message.content)
        
        if len(summaries) > 1:
            combined_summary = "\n\n".join(summaries)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": f"Please create a cohesive, condensed summary from these section summaries:\n\n{combined_summary}"}
                ]
            )
            return response.choices[0].message.content
        
        return summaries[0]

    def create_transcript_doc(self, video_info, transcript):
        """Create a Google Doc transcript file."""
        print(f"Creating transcript doc for: {video_info['title']}")
        
        # Format transcript with paragraphs
        formatted_transcript = self.format_transcript_with_paragraphs(transcript)
        
        # Create Google Doc
        doc_id = self.gdrive.create_doc(
            video_info['title'],
            formatted_transcript,
            video_info
        )
        
        print(f"Created Google Doc with ID: {doc_id}")
        return doc_id
