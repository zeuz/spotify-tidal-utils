# -*- coding: utf-8 -*-
import configparser
import argparse
from ClientSpotify.spotify_client import SpotifyClient
from ClientTidal.tidal_client import TidalClient
import time
import re


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




class SyncLists:
    def __init__(self, spotify_client, tidal_client):
        self.spotify = spotify_client
        self.tidal = tidal_client

    def sync_spotify_to_tidal(self, tidal_playlist_name, spotify_playlist_id):
        # get all tracks from the playlist
        spotify_tracks = self.spotify.get_playlist_tracks(spotify_playlist_id)
        total_listed = len(spotify_tracks)
        print(f"🎶 Spotify playlist has {total_listed} tracks")
        print(f"trying to create Tidal playlist: {tidal_playlist_name}")
        # get current date and time for description
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        tidal_playlist = self.tidal._get_or_create_playlist(tidal_playlist_name,
                                                       description="Created from Spotify {current_time}")
        total_synced = 0
        for artist, title in spotify_tracks:
            print(f"🎵 {artist} – {title}")
            # search for the track in Tidal
            tidal_track = self.tidal.find_best_quality_track(artist, title)
            if tidal_track:
                print(
                    f"✅ Found on TIDAL: {tidal_track.artist.name} – {tidal_track.name}  - Quality: {tidal_track.audio_quality}"
                )
                # add to playlist
                # tidal.add_track_to_playlist_by_id(tidal_playlist, tidal_track.id)
                self.tidal.add_track_to_playlist_by_id(tidal_playlist, tidal_track.id)
                print(f"✅ Added to TIDAL playlist: {tidal_playlist_name} By id : {tidal_track.id}")
                total_synced += 1
            else:
                print(
                    f"❌ Not Found on TIDAL: {title} – {artist}"
                )
        print(f"Total listed on spotify {total_listed} Total synced: {total_synced}")

    def sync_tidal_to_spotify(self, tidal_playlist_name, spotify_playlist_id):
        # get all tracks from the playlist
        tidal_playlist = self.tidal.get_playlist(tidal_playlist_name)
        # print(f"🎶 {len(tidal_playlist)} tracks found on TIDAL")
        tidal_num_tracks = 0
        spotify_num_tracks = 0
        if tidal_playlist:
            tidal_num_tracks = tidal_playlist.num_tracks
            print(f"🎶 Tidal playlist {tidal_playlist_name} has {tidal_num_tracks} tracks")
        else:
            print(f"❌ Tidal playlist {tidal_playlist_name} not found")
            exit(1)
        if tidal_num_tracks > 0:
            for tidal_track in tidal_playlist.items():
                print(f"🎵 {tidal_track.name} – {tidal_track.artist.name}")
                # search for the track in Spotify
                spotify_track = self.spotify.search_track(tidal_track.artist.name, tidal_track.name)

                if not spotify_track:
                    print(
                        f"❌ Not found on SPOTIFY: {tidal_track.name} – {tidal_track.artist.name}"
                    )
                else:
                    print(
                        f"✅ Found on SPOTIFY: {spotify_track['name']} – {spotify_track['artist']}, {spotify_track['id']}"
                    )
                    if self.spotify.add_track_to_playlist(spotify_playlist_id, spotify_track['id']):
                        print(f"✅ Added to Spotify playlist: {spotify_playlist_id} By id : {spotify_track['id']}")
                        spotify_num_tracks += 1

            print(f"Total listed on Tidal {tidal_num_tracks} Total synced: {spotify_num_tracks}")
        else:
            print(f"❌ Tidal playlist {tidal_playlist_name} is empty")
            exit(1)



def main():

    parser = argparse.ArgumentParser(description="Sync Spotify Daily Mix to Tidal")
    parser.add_argument("--spotify", type=str, help="Spotify playlist ID")
    parser.add_argument("--url", type=str, help="Spotify playlist URL (optional, will extract ID)")
    parser.add_argument("--tidal", type=str, help="Tidal playlist name")
    parser.add_argument("--dir", type=str, help=" \n" \
    "T: Tidal -> Spotify \n" \
    "S: Spotify -> Tidal \n" \
    "B: Both (default)\n")

    args = parser.parse_args()
    SYNC_BOTH = False
    DIRECTION_PRIORITY = 'B'

    if args.spotify:
        spotify_playlist_id = f'spotify:playlist:{args.spotify}'
        print(f"Syncing Spotify playlist: {spotify_playlist_id}")
    elif args.url:
        # Extract playlist ID from URL if provided
        match = re.search(r'playlist/([a-zA-Z0-9]+)', args.url)
        if match:
            spotify_playlist_id = f'spotify:playlist:{match.group(1)}'
            print(f"Extracted Spotify playlist ID: {spotify_playlist_id}")
        else:
            print("Invalid Spotify playlist URL format")
            exit(1)

    if args.tidal:
        tidal_playlist_name = args.tidal
        print(f"Syncing Tidal playlist: {tidal_playlist_name}")
    else:
        print("Must provide a Tidal playlist name")
        exit(1)


    if args.dir:
        if args.dir == "T":
            DIRECTION_PRIORITY = 'T'
            print("Sync Tidal to Spotify")
        elif args.dir == "S":
            DIRECTION_PRIORITY = 'S'
            print("Sync Spotify to Tidal")
        elif args.dir == "B":
            DIRECTION_PRIORITY = 'B'
            print("Sync Both")
        else:
            print("Invalid direction, must be T, S or B")
            exit(1)
    else:
        print("Sync Both")
        DIRECTION_PRIORITY = 'B'
    # initialize clients
    print("Initializing spotify client...")
    spotify = SpotifyClient(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
    )
    print("Initializing Tidal client...")
    tidal = TidalClient(session_path=TIDAL_DB_SESSION_PATH)

    sync_lists = SyncLists(spotify, tidal)
    print("Clients initialized successfully.")
    if DIRECTION_PRIORITY == 'B':
        print("Syncing both directions...")
        print("Syncing Spotify to Tidal...")
        sync_lists.sync_spotify_to_tidal(tidal_playlist_name, spotify_playlist_id)
        print("Syncing Tidal to Spotify...")
        sync_lists.sync_tidal_to_spotify(tidal_playlist_name, spotify_playlist_id)
    elif DIRECTION_PRIORITY == 'S':
        sync_lists.sync_spotify_to_tidal(tidal_playlist_name, spotify_playlist_id)
    elif DIRECTION_PRIORITY == 'T':
        sync_lists.sync_tidal_to_spotify(tidal_playlist_name, spotify_playlist_id)


if __name__ == "__main__":
    main()
