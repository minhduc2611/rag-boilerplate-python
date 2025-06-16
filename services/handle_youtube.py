from pytube import YouTube
from typing import Dict, Any
import time
from urllib.error import HTTPError
import re
import json
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter

class YouTubeError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def validate_video_id(video_id: str) -> bool:
    """Validate YouTube video ID format"""
    # YouTube video IDs are typically 11 characters long
    pattern = r'^[a-zA-Z0-9_-]{11}$'
    return bool(re.match(pattern, video_id))

def get_video_metadata(video_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Fetch metadata for a YouTube video with retry logic"""
    if not validate_video_id(video_id):
        raise YouTubeError("Invalid YouTube video ID format", 400)

    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            # Get the video info using a direct request
            url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(url)
            if response.status_code != 200:
                raise YouTubeError(f"Failed to fetch video: HTTP {response.status_code}", response.status_code)

            # Extract the ytInitialData from the response
            match = re.search(r'var ytInitialData = ({.*?});', response.text)
            if not match:
                raise YouTubeError("Could not extract video data", 400)
            
            data = json.loads(match.group(1))
            video_details = data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']
            
            # Extract metadata
            metadata = {
                "title": video_details.get('title', {}).get('runs', [{}])[0].get('text', ''),
                "channelTitle": video_details.get('ownerText', {}).get('runs', [{}])[0].get('text', ''),
                "publishedAt": None,
                "viewCount": video_details.get('viewCount', {}).get('videoViewCountRenderer', {}).get('viewCount', {}).get('simpleText', '0'),
            }

            # Try to get transcript
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['vi'])
                transcript_data = transcript.fetch()
                
                # Format transcript as SRT
                formatter = SRTFormatter()
                metadata["transcript"] = formatter.format_transcript(transcript_data)
            except Exception as e:
                metadata["transcript"] = None
                print(f"Could not fetch transcript: {str(e)}")
            
            return metadata

        except HTTPError as e:
            if e.code == 404:
                raise YouTubeError("Video not found", 404)
            elif e.code == 403:
                raise YouTubeError("Access to video is restricted", 403)
            last_error = e
        except Exception as e:
            last_error = e

        retry_count += 1
        if retry_count < max_retries:
            time.sleep(1)  # Wait 1 second before retrying

    # If we've exhausted all retries, raise the last error
    raise YouTubeError(f"Failed to fetch video metadata after {max_retries} attempts: {str(last_error)}") 