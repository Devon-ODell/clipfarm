import os
from moviepy.editor import VideoFileClip
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
import time
import schedule

# YouTube API setup
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_youtube_service():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json',  # You'll need to obtain this from Google Cloud Console
        SCOPES
    )
    credentials = flow.run_local_server(port=0)
    return build('youtube', 'v3', credentials=credentials)

def split_video(input_path, output_folder):
    video = VideoFileClip(input_path)
    duration = video.duration
    clip_duration = 30  # 30 seconds per clip
    
    clips = []
    for i in range(8):  # 8 clips of 30 seconds each
        start_time = i * clip_duration
        end_time = start_time + clip_duration
        
        clip = video.subclip(start_time, end_time)
        output_path = os.path.join(output_folder, f'clip_{i+1}.mp4')
        clip.write_videofile(output_path)
        clips.append(output_path)
        
    video.close()
    return clips

def upload_to_youtube(youtube, video_path, title, description):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['your_tags_here'],
            'categoryId': '22'  # Category for People & Blogs
        },
        'status': {
            'privacyStatus': 'public'
        }
    }

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    
    response = insert_request.execute()
    return response

def daily_upload():
    # Initialize YouTube service
    youtube = get_youtube_service()
    
    # Get list of videos in the clips folder
    clips_folder = 'clips'
    temp_folder = 'temp_clips'
    os.makedirs(temp_folder, exist_ok=True)
    
    # Get the first video from clips folder
    videos = [f for f in os.listdir(clips_folder) if f.endswith('.mp4')]
    if not videos:
        print("No videos found in clips folder")
        return
    
    video_path = os.path.join(clips_folder, videos[0])
    
    # Split the video into 30-second clips
    clip_paths = split_video(video_path, temp_folder)
    
    # Upload each clip
    for i, clip_path in enumerate(clip_paths):
        title = f"Video Clip {i+1} - {datetime.now().strftime('%Y-%m-%d')}"
        description = "Automatically uploaded video clip"
        
        try:
            upload_to_youtube(youtube, clip_path, title, description)
            print(f"Successfully uploaded {title}")
        except Exception as e:
            print(f"Error uploading {title}: {str(e)}")
        
        # Clean up the temporary clip
        os.remove(clip_path)
    
    # Remove the original video after processing
    os.remove(video_path)

def main():
    # Schedule daily upload at specific time (e.g., 10 AM)
    schedule.every().day.at("10:00").do(daily_upload)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
