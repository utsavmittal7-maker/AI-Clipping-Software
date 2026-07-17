"""
Optional Google Drive upload for finished clips.

Uses the OAuth "installed app" flow: on first use it opens a browser so you can
authorize access, then caches a token so later runs are silent. Requires a
Google OAuth client file (credentials.json) downloaded from Google Cloud
Console - see the README for the one-time setup.

Everything degrades gracefully: if Drive isn't set up or a call fails, clips are
simply kept locally and a helpful message is printed - the render never breaks.
"""
import os

# 'drive.file' only grants access to files THIS app creates. It's the safest
# scope and does not require Google to verify the app.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class DriveUploader:
    def __init__(self, credentials_path='credentials.json', token_path='token.json',
                 folder_id='', make_shareable=False):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.folder_id = (folder_id or '').strip()
        self.make_shareable = make_shareable
        self.service = None
        self.enabled = False

    def connect(self):
        """Authenticate and build the Drive service. Returns True on success."""
        if not os.path.exists(self.credentials_path):
            print(f"⚠️ Google Drive upload is enabled but '{self.credentials_path}' "
                  f"was not found. Follow the Drive setup steps in the README. "
                  f"Clips will be kept locally.")
            return False
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            print("⚠️ Google API libraries missing. Run: pip install -r requirements.txt")
            return False

        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    print("🔐 Opening your browser to authorize Google Drive access...")
                    creds = flow.run_local_server(port=0)
                with open(self.token_path, 'w', encoding='utf-8') as fh:
                    fh.write(creds.to_json())
            except Exception as e:
                print(f"⚠️ Google Drive authorization failed: {e}. Clips kept locally.")
                return False

        try:
            self.service = build('drive', 'v3', credentials=creds)
            self.enabled = True
            print("✅ Connected to Google Drive")
            return True
        except Exception as e:
            print(f"⚠️ Could not connect to Google Drive: {e}. Clips kept locally.")
            return False

    def upload(self, file_path):
        """Upload one file to Drive. Returns its view link, or None on failure."""
        if not self.enabled or not self.service or not os.path.exists(file_path):
            return None
        try:
            from googleapiclient.http import MediaFileUpload
            metadata = {'name': os.path.basename(file_path)}
            if self.folder_id:
                metadata['parents'] = [self.folder_id]
            media = MediaFileUpload(file_path, resumable=True)
            created = self.service.files().create(
                body=metadata, media_body=media,
                fields='id, webViewLink').execute()

            if self.make_shareable:
                try:
                    self.service.permissions().create(
                        fileId=created['id'],
                        body={'role': 'reader', 'type': 'anyone'}).execute()
                except Exception:
                    pass
            return created.get('webViewLink')
        except Exception as e:
            print(f"    ⚠️ Drive upload failed for {os.path.basename(file_path)}: {e}")
            return None
