import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-read-private user-read-playback-state user-read-currently-playing",
            )
        )

    def get_playlist_tracks(self, playlist_id):
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []
        for item in results["items"]:
            track = item["track"]
            if track:
                artist = track["artists"][0]["name"]
                name = track["name"]
                tracks.append((artist, name))
        return tracks

    def get_current_playing_track(self):
        current = self.sp.current_playback()
        if current and current["is_playing"]:
            item = current["item"]
            artist = item["artists"][0]["name"]
            title = item["name"]
            return artist, title
        else:
            return None
