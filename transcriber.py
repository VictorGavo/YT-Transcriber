import os
import whisper
from openai import OpenAI
from datetime import datetime
import tiktoken
from config import (
    OPENAI_API_KEY,
    TRANSCRIPTS_DIR,
    OBSIDIAN_VAULT_DIR,
    MARKDOWN_TEMPLATE,
    GOOGLE_DRIVE_DIR
)

class VideoTranscriber:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        # Create necessary directories if they don't exist
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        os.makedirs(GOOGLE_DRIVE_DIR, exist_ok=True)
        
        # Define category folders
        self.categories = {
            'time': 'Time Management',
            'relationship': 'Relationships and Network',
            'network': 'Relationships and Network',
            'mindset': 'Mindset and Philosophy',
            'philosophy': 'Mindset and Philosophy',
            'unsorted': 'Unsorted'
        }

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
                {"role": "system", "content": "You are a helpful assistant that formats text into clear, readable paragraphs. Keep the original content intact but add appropriate paragraph breaks for better readability."},
                {"role": "user", "content": f"Please format this transcript into clear paragraphs, maintaining all original content:\n\n{transcript}"}
            ]
        )
        return response.choices[0].message.content

    def determine_category(self, title, transcript):
        """Determine the appropriate category folder based on content."""
        print("Determining content category...")
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that categorizes content. Available categories: Time Management, Relationships and Network, Mindset and Philosophy. If unsure, respond with 'Unsorted'."},
                {"role": "user", "content": f"Based on this title and transcript excerpt, which category best fits? Title: {title}\n\nTranscript excerpt: {transcript[:1000]}"}
            ]
        )
        
        category_text = response.choices[0].message.content.lower()
        
        # Match with available categories
        for key, category in self.categories.items():
            if key in category_text:
                return category
        
        return 'Unsorted'

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

    def extract_highlights(self, transcript):
        """Extract key highlights and insights from the transcript using OpenAI."""
        print("Extracting highlights...")
        
        chunks = self.chunk_text(transcript)
        all_highlights = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Processing chunk {i}/{len(chunks)}...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts key insights and memorable quotes from video transcripts. Format them as bullet points."},
                    {"role": "user", "content": f"Please extract the most important insights, key points, and memorable quotes from the following transcript section. Format them as bullet points:\n\n{chunk}"}
                ]
            )
            all_highlights.append(response.choices[0].message.content)
        
        if len(all_highlights) > 1:
            combined_highlights = "\n\n".join(all_highlights)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that consolidates and refines key points and insights."},
                    {"role": "user", "content": f"Please consolidate and refine these highlights into a clear, non-redundant list of the most important points:\n\n{combined_highlights}"}
                ]
            )
            return response.choices[0].message.content
        
        return all_highlights[0]

    def create_obsidian_note(self, video_info, transcript):
        """Create a formatted transcript file in Google Drive."""
        print(f"Creating transcript for: {video_info['title']}")
        
        # Format transcript with paragraphs
        formatted_transcript = self.format_transcript_with_paragraphs(transcript)
        
        # Generate summary and highlights
        summary = self.generate_summary(transcript)
        highlights = self.extract_highlights(transcript)

        # Get current datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Determine category and create full path
        category = self.determine_category(video_info['title'], transcript)
        category_dir = os.path.join(GOOGLE_DRIVE_DIR, category)
        os.makedirs(category_dir, exist_ok=True)

        # Create content with metadata and formatted sections
        content = f"""Title: {video_info['title']}
Date: {current_time}
Channel: {video_info['channel']}
URL: {video_info['url']}
Category: {category}

SUMMARY
{summary}

TRANSCRIPT
{formatted_transcript}

KEY HIGHLIGHTS
{highlights}
"""

        # Create filename from video title (sanitized)
        filename = "".join(x for x in video_info['title'] if x.isalnum() or x in (' ', '-', '_'))
        filename = f"{filename}.txt"
        filepath = os.path.join(category_dir, filename)

        # Save the file
        print(f"Saving transcript to: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath
