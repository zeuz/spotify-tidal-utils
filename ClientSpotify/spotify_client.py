import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        # https://developer.spotify.com/documentation/web-api/concepts/scopes
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-read-private playlist-modify-private playlist-modify-public user-read-playback-state user-read-currently-playing",
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
    
    def search_track(self, artist, title):
        query = f"artist:{artist} track:{title}"
        results = self.sp.search(q=query, type="track", limit=1)
        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]
            return {
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "uri": track["uri"]
            }
        return None
    
    def add_track_to_playlist(self, playlist_id, track_id):
        # Check if the track is already in the playlist
        existing_tracks = self.sp.playlist_tracks(playlist_id)
        existing_track_ids = {item["track"]["id"] for item in existing_tracks["items"]}
        if track_id in existing_track_ids:
            print(f"🔁 Track {track_id} is already in playlist {playlist_id}")
            return
        # Add the track to the playlist        
        try:
            self.sp.playlist_add_items(playlist_id, [track_id])
            return True
        except Exception as e:
            print(f"❌ Error adding track to playlist: {e}")
        return False
