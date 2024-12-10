import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
import io
from datetime import datetime
import re
from config import (
    GOOGLE_DRIVE_CREDS_FILE,
    GDRIVE_UNREAD_FOLDER_ID,
    GDRIVE_PROCESSED_FOLDER_ID,
    OBSIDIAN_VAULT_PATH,
    GDRIVE_DOC_TEMPLATE,
    OBSIDIAN_NOTE_TEMPLATE
)

class GoogleDriveHandler:
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)

    def _get_credentials(self):
        """Get valid credentials for Google Drive API."""
        creds = None
        token_path = 'token.pickle'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_DRIVE_CREDS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def create_doc(self, title, content, video_info):
        """Create a new Google Doc in the unread folder."""
        doc_metadata = {
            'name': title,
            'parents': [GDRIVE_UNREAD_FOLDER_ID],
            'mimeType': 'application/vnd.google-apps.document'
        }

        # Create empty doc
        doc = self.service.files().create(body=doc_metadata).execute()
        doc_id = doc.get('id')

        # Format content using template
        doc_content = GDRIVE_DOC_TEMPLATE.format(transcript=content)

        # Update doc content
        requests = [{
            'insertText': {
                'location': {'index': 1},
                'text': doc_content
            }
        }]

        self.docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()

        return doc_id

    def _extract_highlights(self, doc_content):
        """Extract highlighted text and comments from Google Doc content."""
        highlights = []
        
        # Extract text with background color (highlights)
        if 'backgroundColorStyle' in str(doc_content):
            elements = doc_content.get('body', {}).get('content', [])
            for element in elements:
                paragraph = element.get('paragraph', {})
                elements = paragraph.get('elements', [])
                for elem in elements:
                    if elem.get('textRun', {}).get('textStyle', {}).get('backgroundColorStyle'):
                        text = elem.get('textRun', {}).get('content', '').strip()
                        if text:
                            highlights.append(f"- {text}")

        # Extract comments
        comments = self.docs_service.documents().get(
            documentId=doc_content['documentId'],
            suggestionsViewMode='PREVIEW_WITHOUT_SUGGESTIONS'
        ).execute()
        
        for comment in comments.get('replies', []):
            content = comment.get('content', '').strip()
            if content:
                highlights.append(f"- Comment: {content}")

        return "\n".join(highlights) if highlights else "No highlights or comments found."

    def check_for_processed_files(self):
        """Check for files moved to the processed folder and convert them."""
        # Query files in processed folder
        results = self.service.files().list(
            q=f"'{GDRIVE_PROCESSED_FOLDER_ID}' in parents",
            fields="files(id, name, createdTime)"
        ).execute()

        for file in results.get('files', []):
            # Get the document content
            doc = self.docs_service.documents().get(documentId=file['id']).execute()
            
            # Extract highlights and full content
            highlights = self._extract_highlights(doc)
            full_content = self._extract_full_content(doc)
            
            # Create markdown file
            self._create_markdown_note(
                file['name'],
                highlights,
                full_content,
                file['createdTime']
            )
            
            # Move file to archive or delete
            self.service.files().delete(fileId=file['id']).execute()

    def _extract_full_content(self, doc):
        """Extract full content from Google Doc."""
        content = []
        elements = doc.get('body', {}).get('content', [])
        
        for element in elements:
            paragraph = element.get('paragraph', {})
            elements = paragraph.get('elements', [])
            for elem in elements:
                if 'textRun' in elem:
                    content.append(elem['textRun']['content'])
        
        return ''.join(content)

    def _create_markdown_note(self, title, highlights, content, created_date):
        """Create markdown note in Obsidian vault."""
        # Clean title for filename
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[-\s]+', '-', clean_title).strip('-')
        
        # Format dates
        created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        processed_date = datetime.now()

        # Format content using template
        md_content = OBSIDIAN_NOTE_TEMPLATE.format(
            created_date=created_date.strftime('%Y-%m-%d %H:%M:%S'),
            processed_date=processed_date.strftime('%Y-%m-%d %H:%M:%S'),
            highlights=highlights,
            transcript=content,
            summary="", # Could be generated using OpenAI if needed
            url="",  # Would need to be passed from video info
            channel=""  # Would need to be passed from video info
        )

        # Save markdown file
        filepath = os.path.join(OBSIDIAN_VAULT_PATH, f"{clean_title}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def monitor_drive(self):
        """Main monitoring function to be run periodically."""
        self.check_for_processed_files()
