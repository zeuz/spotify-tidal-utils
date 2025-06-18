import tidalapi
from tinydb import TinyDB
import base64
# docs: https://tidalapi.netlify.app/


class TidalClient:
    def __init__(self, session_path):
        self.session = tidalapi.Session()
        self.db_path = session_path

        if not self._load_session_tokens():
            self.session.login_oauth_simple()
            self._save_session_tokens()


    def _encode(self, s):
        return base64.b64encode(str(s).encode()).decode()

    def _decode(self, s):
        return base64.b64decode(s.encode()).decode()

    def _save_session_tokens(self):
        db = TinyDB(self.db_path)
        db.truncate()
        db.insert(
            {
                "token_type": self._encode(self.session.token_type),
                "access_token": self._encode(self.session.access_token),
                "refresh_token": self._encode(self.session.refresh_token),
                "expiry_time": self._encode(self.session.expiry_time),
            }
        )

    def _load_session_tokens(self):
        db = TinyDB(self.db_path)
        tokens = db.all()
        if not tokens:
            return False
        t = tokens[0]
        try:
            self.session.load_oauth_session(
                token_type=self._decode(t["token_type"]),
                access_token=self._decode(t["access_token"]),
                refresh_token=self._decode(t["refresh_token"]),
                expiry_time=self._decode(t["expiry_time"]),
            )
        except Exception as e:
            print(f"Loading session error: {e}")
            return False
        return True

    def _get_or_create_playlist(self, name, description):
        for p in self.session.user.playlists():
            if p.name == name:
                return p
        return self.session.user.create_playlist(name, description=description)
    
    def get_playlist(self, name, description=None):         
        for p in self.session.user.playlists():
            if p.name == name:
                return p
        return None
    
    def force_create_playlist(self, name, description):
        for p in self.session.user.playlists():
            if p.name == name:
                print(f"Playlist {name} already exists.")
                print(f"ID: {p.id}")
                print(f"deleted...")
                p.delete()

        print(f"Creating playlist {name}.")
        return self.session.user.create_playlist(name, description=description)

    def find_track(self, artist, title):
        results = self.session.search(
            f"{artist} {title}", models=[tidalapi.models.Track]
        )
        if results.tracks:
            return results.tracks[0]
        return None

    def find_best_quality_track(self, artist, title):
        query = f"{artist} {title}"
        results = self.session.search(query)
        tracks = results["tracks"]

        if not tracks:
            print(f"Not found: {artist} – {title}")
            return None

        # Ordenamos por calidad descendente
        quality_order = ["LOW", "HIGH", "LOSSLESS", "HI_RES"]
        quality_score = {q: i for i, q in enumerate(quality_order)}

        best_track = max(tracks, key=lambda t: quality_score.get(t.audio_quality, 0))
        # print(f"🎵 {best_track.artist.name} – {best_track.name} ({best_track.audio_quality})")
        return best_track

    def add_tracks_to_playlist(self, tracks):
        existing_ids = {track.id for track in self.playlist.tracks()}
        added = 0
        for artist, title in tracks:
            tidal_track = self.find_track(artist, title)
            if not tidal_track:
                print(f"❌ Not found on TIDAL: {artist} – {title}")
                continue
            if tidal_track.id in existing_ids:
                print(f"🔁 Already on playlist: {artist} – {title}")
                continue
            self.playlist.add([tidal_track.id])
            print(f"🎵 Added: {artist} – {title}")
            added += 1
        print(f"✅ {added} new tracks added to the playlist.")

    def add_track_to_playlist_by_id(self, playlist, track_id):
        for track in playlist.tracks():
            if track.id == track_id:
                print(f"🔁 Already on the playlist {track.name}")
                return track.id
        playlist.add([track_id])
        print(f"🎵 Added to Tidal by: {track_id}")

    def remove_all_tracks_from_playlist(self, playlist):
        for track in playlist.tracks():
            playlist.remove_by_id(track.id)
            print(f"❌ Removed: {track.name}")

