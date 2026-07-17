# YouTube Viral Clipper

**Transform any YouTube video into captivating, shareable short-form clips with the YouTube Viral Clipper.** This free and open-source software leverages AI to automate the entire video clipping process, making viral content creation accessible to everyone.

## Features

- **AI-Powered Clip Selection**: Automatically identifies the most engaging and viral-worthy moments in a video.
- **Smart Face Tracking**: Keeps the speaker perfectly framed, even in dynamic scenes.
- **Engaging Captions**: Adds word-by-word captions in various styles to boost viewer retention.
- **Easy Configuration**: Simple setup with a `.env` file for your API keys and preferences.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/youtube-viral-clipper.git
   cd youtube-viral-clipper
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment:**
   Copy the `.env.example` file to `.env` and add your Gemini API key.
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and add your API key:
   ```
   GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
   ```

## Usage

Run the `main.py` script from your terminal:
```bash
python main.py
```
The script will prompt you for the YouTube URL and other options. The generated clips will be saved in the `clips` directory.

## Upload clips to Google Drive (optional)

The app can upload each finished clip straight to your Google Drive. This needs
a one-time authorization so the app is allowed to write to *your* Drive.

**One-time setup:**

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and
   create a new project (top bar → project dropdown → *New Project*).
2. In the search bar, open **APIs & Services → Library**, search for
   **Google Drive API**, and click **Enable**.
3. Open **APIs & Services → OAuth consent screen**. Choose **External**, fill in
   an app name and your email, and under **Test users** add your own Google
   account email. Save.
4. Open **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   Choose **Desktop app**, create it, then **Download JSON**.
5. Rename the downloaded file to **`credentials.json`** and place it in the
   project folder (next to `main.py`).
6. In your `.env`, set:
   ```
   UPLOAD_TO_DRIVE="true"
   # Optional: paste a folder id from a Drive folder URL to upload into it
   DRIVE_FOLDER_ID=""
   ```

The **first** time you run with uploads enabled, a browser window opens asking
you to sign in and allow access (you may see an "unverified app" notice — click
*Advanced → Continue* since it's your own app). A `token.json` is then saved so
future runs upload silently.

Other Drive options in `.env`: `DELETE_AFTER_UPLOAD` (remove the local copy once
uploaded) and `DRIVE_MAKE_SHAREABLE` (make each clip viewable by link).

The app only ever accesses files it creates (the `drive.file` scope) — it cannot
see the rest of your Drive.

## Troubleshooting

If you encounter issues downloading YouTube videos, try the following:

- **Use a custom user agent**: Set a custom user agent in your `.env` file to improve download reliability.
- **Update pytube**: YouTube frequently changes its platform, so keeping `pytube` updated can help:
  ```bash
  pip install -U pytube
  ```
- **Check video availability**: Ensure the video is publicly available and not age-restricted or private.
