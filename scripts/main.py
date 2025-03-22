import os
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Environment variables (set in GitHub Secrets)
CLIENT_ID = os.environ['GDRIVE_CLIENT_ID']
CLIENT_SECRET = os.environ['GDRIVE_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['GDRIVE_REFRESH_TOKEN']
DRIVE_FOLDER_ID = os.environ['DRIVE_FOLDER_ID']
ARCHIVE_FOLDER_ID = os.environ['ARCHIVE_FOLDER_ID']

def get_credentials():
    return Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri='https://oauth2.googleapis.com/token',
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/youtube.upload'
        ]
    )

def main():
    # Authenticate services
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    youtube_service = build('youtube', 'v3', credentials=creds)

    # Get random video
    results = drive_service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType contains 'video/'",
        fields="files(id, name)"
    ).execute()
    
    if not results.get('files'):
        print("No videos found")
        return

    video = random.choice(results['files'])
    
    # Download video
    request = drive_service.files().get_media(fileId=video['id'])
    filename = f"temp_{video['name']}"
    with open(filename, 'wb') as f:
        f.write(request.execute())

    # Upload to YouTube
    media = MediaFileUpload(filename, chunksize=-1, resumable=True)
    request = youtube_service.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": video['name'],
                "description": "Auto-uploaded short",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media
    )
    response = request.execute()
    print(f"Uploaded video ID: {response['id']}")

    # Move to archive
    drive_service.files().update(
        fileId=video['id'],
        addParents=ARCHIVE_FOLDER_ID,
        removeParents=DRIVE_FOLDER_ID,
        fields='id, parents'
    ).execute()

    # Cleanup
    os.remove(filename)

if __name__ == "__main__":
    main()
