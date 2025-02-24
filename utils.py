import os
import random
import json

VIDEO_FOLDER = "static/videos"
VIDEO_TRACKER = "static/videos_tracker.json"

def get_daily_video():
    """
    Returns a unique video for the day, ensuring no repeats until all videos are shown.
    """
    # Lade alle verfügbaren Videos
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")]
    if not videos:
        return None  # Kein Video verfügbar

    # Lade den Tracker oder initialisiere ihn
    if os.path.exists(VIDEO_TRACKER):
        with open(VIDEO_TRACKER, "r") as tracker_file:
            watched_videos = json.load(tracker_file)
    else:
        watched_videos = []

    # Finde die ungesehenen Videos
    unwatched_videos = [video for video in videos if video not in watched_videos]

    if not unwatched_videos:
        # Wenn alle Videos gesehen wurden, starte von vorne
        watched_videos = []
        unwatched_videos = videos

    # Wähle ein zufälliges Video aus den ungesehenen
    chosen_video = random.choice(unwatched_videos)
    watched_videos.append(chosen_video)

    # Speichere den aktualisierten Tracker
    with open(VIDEO_TRACKER, "w") as tracker_file:
        json.dump(watched_videos, tracker_file)

    return f"/{VIDEO_FOLDER}/{chosen_video}"
