"""YouTube Data API v3 client using standard HTTP requests."""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

from .oauth import get_access_token

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"


class YouTubeClient:
    def __init__(self, access_token: Optional[str] = None, timeout: float = 30.0):
        self._access_token = access_token
        self._timeout = timeout

    @property
    def access_token(self) -> Optional[str]:
        if not self._access_token:
            self._access_token = get_access_token()
        return self._access_token

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def _headers(self) -> Dict[str, str]:
        token = self.access_token
        if not token:
            raise RuntimeError("YouTube API not authorized: access token is missing.")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def list_my_playlists(self) -> List[Dict[str, Any]]:
        """List current channel's playlists."""
        url = f"{YOUTUBE_API_BASE}/playlists"
        params = {"part": "snippet,id", "mine": "true", "maxResults": 50}
        response = requests.get(url, headers=self._headers(), params=params, timeout=self._timeout)
        response.raise_for_status()
        return response.json().get("items", [])

    def create_playlist(
        self, title: str, description: str = "", privacy_status: str = "unlisted"
    ) -> str:
        """Create a new playlist and return its ID."""
        url = f"{YOUTUBE_API_BASE}/playlists"
        params = {"part": "snippet,status"}
        payload = {
            "snippet": {
                "title": title,
                "description": description or f"Learn platformasi: {title}",
            },
            "status": {
                "privacyStatus": privacy_status,
            },
        }
        response = requests.post(
            url, headers=self._headers(), params=params, json=payload, timeout=self._timeout
        )
        response.raise_for_status()
        return response.json()["id"]

    def find_or_create_playlist(
        self, title: str, description: str = "", privacy_status: str = "unlisted"
    ) -> str:
        """Find an existing playlist by title or create one if it doesn't exist."""
        playlists = self.list_my_playlists()
        for p in playlists:
            snippet = p.get("snippet", {})
            if snippet.get("title", "").strip().lower() == title.strip().lower():
                return p["id"]

        return self.create_playlist(title, description, privacy_status)

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str = "",
        privacy_status: str = "unlisted",
    ) -> str:
        """Upload a video file to YouTube and return the video ID.

        Uses the resumable upload protocol.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        file_size = os.path.getsize(file_path)

        # Step 1: Initiate resumable session
        init_url = f"{YOUTUBE_UPLOAD_BASE}/videos"
        params = {"uploadType": "resumable", "part": "snippet,status"}
        headers = self._headers()
        headers["X-Upload-Content-Type"] = "video/*"
        headers["X-Upload-Content-Length"] = str(file_size)

        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "27",  # Education category
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        init_res = requests.post(
            init_url,
            headers=headers,
            params=params,
            json=metadata,
            timeout=self._timeout,
        )
        init_res.raise_for_status()
        upload_location = init_res.headers.get("Location")
        if not upload_location:
            raise RuntimeError("YouTube upload initiation failed: missing Location header.")

        # Step 2: Upload file bytes
        with open(file_path, "rb") as f:
            upload_headers = {
                "Content-Length": str(file_size),
                "Content-Type": "video/*",
            }
            upload_res = requests.put(
                upload_location,
                headers=upload_headers,
                data=f,
                timeout=max(self._timeout * 4, 120.0),
            )
            upload_res.raise_for_status()
            return upload_res.json()["id"]

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> None:
        """Add a video to a YouTube playlist."""
        url = f"{YOUTUBE_API_BASE}/playlistItems"
        params = {"part": "snippet"}
        payload = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        }
        response = requests.post(
            url, headers=self._headers(), params=params, json=payload, timeout=self._timeout
        )
        response.raise_for_status()
