import os
import io
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send'
]

class MemoryHandler:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.drive_service = None
        self.local_memory_dir = os.path.join(os.getcwd(), "Eve_Memories_Local")
        os.makedirs(self.local_memory_dir, exist_ok=True)
        self._authenticate()

    def _authenticate(self):
        """Authenticates with Google APIs using OAuth2 credentials.json."""
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token.json: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh Google OAuth token: {e}")
                    creds = None
            
            if not creds and os.path.exists(self.credentials_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(self.token_path, 'w') as token_file:
                        token_file.write(creds.to_json())
                    logger.info("Successfully authenticated with Google OAuth APIs.")
                except Exception as e:
                    logger.error(f"Error during Google OAuth flow: {e}")
                    creds = None

        if creds and creds.valid:
            try:
                self.drive_service = build('drive', 'v3', credentials=creds)
                logger.info("Google Drive service initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to build Google Drive service: {e}")

    def _get_or_create_memories_folder(self) -> str:
        """Finds or creates the 'Eve_Memories' folder in Google Drive root."""
        if not self.drive_service:
            return None

        try:
            # Query for existing folder
            query = "name = 'Eve_Memories' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])

            if files:
                return files[0]['id']

            # Create folder if it doesn't exist
            folder_metadata = {
                'name': 'Eve_Memories',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
            logger.info(f"Created 'Eve_Memories' folder on Google Drive (ID: {folder.get('id')}).")
            return folder.get('id')
        except Exception as e:
            logger.error(f"Error accessing Google Drive folder: {e}")
            return None

    def save_memory(self, topic: str, text: str) -> str:
        """Saves a note to Google Drive (or local fallback if unauthenticated)."""
        safe_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        filename = f"{safe_topic}.txt"

        # Try Google Drive first
        folder_id = self._get_or_create_memories_folder()
        if self.drive_service and folder_id:
            try:
                file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }
                media = MediaIoBaseUpload(io.BytesIO(text.encode('utf-8')), mimetype='text/plain')
                file = self.drive_service.files().create(
                    body=file_metadata, media_body=media, fields='id'
                ).execute()
                logger.info(f"Memory saved to Google Drive: '{filename}' (ID: {file.get('id')}).")
                return f"Memory regarding '{topic}' saved successfully to your Google Drive in Eve_Memories."
            except Exception as e:
                logger.error(f"Failed to save memory to Google Drive: {e}")

        # Local fallback
        local_path = os.path.join(self.local_memory_dir, filename)
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Memory saved locally: '{local_path}'.")
            return f"Memory regarding '{topic}' saved locally in Eve_Memories_Local."
        except Exception as e:
            return f"Failed to save memory: {str(e)}"

    def search_memory(self, query: str) -> str:
        """Searches saved memory files in Google Drive (or local fallback)."""
        results_text = []

        folder_id = self._get_or_create_memories_folder()
        if self.drive_service and folder_id:
            try:
                q = f"'{folder_id}' in parents and trashed = false"
                response = self.drive_service.files().list(q=q, fields="files(id, name)").execute()
                files = response.get('files', [])

                for f in files:
                    if query.lower() in f['name'].lower():
                        request = self.drive_service.files().get_media(fileId=f['id'])
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        content = fh.getvalue().decode('utf-8', errors='ignore')
                        results_text.append(f"[{f['name']}]: {content}")
            except Exception as e:
                logger.error(f"Error searching Google Drive memories: {e}")

        # Local fallback search
        if os.path.exists(self.local_memory_dir):
            for fname in os.listdir(self.local_memory_dir):
                if query.lower() in fname.lower():
                    try:
                        with open(os.path.join(self.local_memory_dir, fname), "r", encoding="utf-8") as f:
                            results_text.append(f"[{fname} (Local)]: {f.read()}")
                    except Exception:
                        pass

        if results_text:
            return "\n".join(results_text)
        else:
            return f"No memories found matching query '{query}'."
