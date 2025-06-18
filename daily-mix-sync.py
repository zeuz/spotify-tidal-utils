# -*- coding: utf-8 -*-
import configparser
import argparse
from ClientSpotify.spotify_client import SpotifyClient
from ClientTidal.tidal_client import TidalClient
import time


SPOTIFY_CLIENT_ID = None
SPOTIFY_CLIENT_SECRET = None
SPOTIFY_REDIRECT_URI = None
TIDAL_DB_SESSION_PATH = None

try:
    config = configparser.ConfigParser()
    config.read("config.cfg")
    SPOTIFY_CLIENT_ID = config.get("spotify", "client_id")
    SPOTIFY_CLIENT_SECRET = config.get("spotify", "client_secret")
    SPOTIFY_REDIRECT_URI = config.get("spotify", "redirect_uri")
    TIDAL_DB_SESSION_PATH = config.get("tidal", "db_session_path")
except Exception as e:
    print(f"Error on load config file: {e}")
    exit(1)


def main():
    # receive arguments opcionally nombre del playlist
    delete_playlist_content = True
    refresh_time = 30

    parser = argparse.ArgumentParser(description="Sync Spotify Daily Mix to Tidal")
    parser.add_argument("--playlist", type=str, help="Tidal Playlist name")
    parser.add_argument(
        "--no-clear", action="store_true", help="Clean Tidal playlist before adding new tracks"
    )
    parser.add_argument("--refresh", type=int, help="Refresh time")

    args = parser.parse_args()

    # Check if the playlist name is provided
    if args.playlist:
        tidal_playlist_name = args.playlist
    else:
        tidal_playlist_name = "spotify-daily-mix"
    if args.no_clear:
        delete_playlist_content = False
        print("Param: Not clear list")
    if args.refresh:
        refresh_time = args.refresh
        print(f"Param: Refresh on {refresh_time} seconds")

    # initialize clients
    spotify = SpotifyClient(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
    )
    #
    tidal = TidalClient(session_path=TIDAL_DB_SESSION_PATH)
    description = "From Spotify Daily Mix"
    print(f"Trying creating list on TIDAL: {tidal_playlist_name}")
    tidal_playlist = tidal._get_or_create_playlist(tidal_playlist_name, description)
    if not tidal_playlist:
        print(f"Error on load Tidal playlist: {tidal_playlist_name}")
        exit(1)
    if tidal_playlist and delete_playlist_content:
        print(f"Cleaning TIDAL playlist: {tidal_playlist.name}")
        tidal.remove_all_tracks_from_playlist(tidal_playlist)
    local_current_song = ""
    local_previous_song = ""
    while True:
        # Get the current song from Spotify
        spotify_current_song = spotify.get_current_playing_track()

        if spotify_current_song:
            artist, title = spotify_current_song
            local_current_song = f"{artist}-{title}".encode("utf-8")
            print(f"🎶 Playing on Spotify: {artist} – {title}")
            # search for the track in Tidal
            if local_current_song == local_previous_song:
                print("Track already processed, waiting...")
            else:
                print(f"Searching for TIDAL best quality: {artist} – {title}")
                tidal_track = tidal.find_best_quality_track(artist, title)
                if tidal_track:
                    print(
                        f"✅ Found on TIDAL: {tidal_track.artist.name} – {tidal_track.name}  - Quality: {tidal_track.audio_quality}"
                    )
                    # add to playlist
                    tidal.add_track_to_playlist_by_id(tidal_playlist, tidal_track.id)
                else:
                    print(
                        f"❌ No found on TIDAL: {artist} – {title}"
                    )
                # update previous song
                local_previous_song = local_current_song
        else:
            print("❌ No track Spotify playing")
        # Wait for a while before checking again
        time.sleep(refresh_time)  # Check every minute


if __name__ == "__main__":
    main()
