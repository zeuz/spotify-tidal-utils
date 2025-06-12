# -*- coding: utf-8 -*-
import argparse
import copy
from ClientTidalHiFi.tidalhifi_client import  TidalHiFiClient
from QueueConverter.task_queue import TaskQueue
from QueueConverter.consumer import Consumer
import time
import re
import subprocess
import uuid
import os



class Recorder:
    def __init__(self, task_queue, is_check_interface=False):
        self.task_queue = task_queue
        self.recording = False
        self.tmp_filename = None
        self.original_filename = None  # Placeholder for the original filename if needed
        self.is_check_interface = is_check_interface  # Flag to check if the interface is being used

    def _check_if_file_exists(self, filename):
        return os.path.isfile(filename)

    def start_recording(self):
        # process in background with subprocess and this command arecord -D hw:0,1 -f S32_LE -r 48000 -c 2 tmp.wav
        self.tmp_filename = f"tmp-rec-{uuid.uuid4()}.wav"  # Unique filename for each recording
        print(f"Recording {self.tmp_filename} started...")
        if not self.is_check_interface:
            subprocess.Popen(["arecord", "-D", "hw:0,1", "-f", "S16_LE", "-r", "44100", "-c", "2", self.tmp_filename])
        self.recording = True

        return self.tmp_filename  # Return the filename for reference, if needed

    def stop_recording(self, original_filename=None, art_url=None, artist_name=None,
                       track_name=None, default_album='', clean_art_file=False):
        print(f"Recording {self.tmp_filename} stopped...")
        if self._check_if_file_exists(f'{original_filename}.flac'):
            print(f"File {original_filename}.flac already exists, skipping processing.")
            subprocess.run(["pkill", "-f", "arecord"])
            self.recording = False
            os.unlink(self.tmp_filename)  # Remove the temporary file
            return

        if not self.is_check_interface:
            subprocess.run(["pkill", "-f", "arecord"])  # Stops the arecord process
            self.recording = False
            self.task_queue.add_task({'tmp_file_name':self.tmp_filename,
                                      'original_file_name':original_filename,
                                      'art_url':art_url,
                                      'artist_name':artist_name,
                                      'track_name':track_name,
                                      'default_album':default_album,
                                      'clean_art_file':clean_art_file})  # Add the filename to the task queue for further processing





def main():
    parser = argparse.ArgumentParser(description="Tidal playlist to FLAC, on linux with tidal-hifi")
    #only one argument mandatory always playlist-name
    parser.add_argument("--url", type=str, help="Url Tidal hifi", required=False)
    parser.add_argument("--check", action="store_true", help="Check if TIDAL hifi UI its changing the song name", required=False)
    parser.add_argument("--art-file", action="store_true", help="Preserve art files", required=False)
    parser.add_argument("--album",  type=str, help="Set default album to organize like playlist on devices", required=False)
    args = parser.parse_args()
    url = None
    check_interface = False
    clean_art_file = True  # Default
    default_album = ""
    if not args.url:
        url = "http://127.0.0.1:47836"
    else:
        url = args.url
        #check if url is valid with regex ej: http://127.0.0.1:4345
        if not re.match(r"http://127\.0\.0\.1:\d{4}", url):
            print("Error: Invalid param url must be http://host:port")
            return
    if args.check:
        check_interface  = True

    if args.art_file:
        print("Param: No clean art file")
        clean_art_file = False

    if args.album:
        default_album = args.album
        print(f"Param: Default album set to {default_album}")

    # initialize clients
    tidalui =  TidalHiFiClient(url)
    task_queue = TaskQueue()
    consumer = Consumer(task_queue)
    consumer.start()
    recorder = Recorder(task_queue, check_interface)
    #while until ctrl+c
    recorder.start_recording()  # Start recording in the background
    tidalui.play()

    track_id = None
    previous_track_id = ""
    previous_track_name = ""
    previous_track_data = None
    current_track_id = ""
    first_run = True
    cont_playing = 0
    while True:
        try:
            cont_playing += 1
            now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            current_song_data = tidalui.get_current_song_data()
            # print(current_song_data)
            """
            {'title': 'Forgiven', 'artists': 'Alexis Ffrench', 
            'album': '', 'icon': '/home/zeuz/.config/tidal-hifi/notification.jpg',
             'playingFrom': '', 'status': 'playing', 
             'url': 'https://tidal.com/browse/track/94072682?u', 
             'current': '0:05', 'currentInSeconds': 5, 'duration': '', 
             'durationInSeconds': 0, 
             'image': 'https://resources.tidal.com/images/72cb7592/255a/44b7/ac9c/625b9a0543d9/640x640.jpg', 
             'favorite': False, 'player': {'status': 'playing', 'shuffle': False, 'repeat': 'off'}, 
             'artist': 'Alexis Ffrench'}

            """

            # re  extract track id from url like https://tidal.com/browse/track/94072682?u

            if current_song_data:
                current_song = current_song_data['title'] + " - " + current_song_data['artists']
                song_url = current_song_data['url']

                if song_url:
                    match = re.search(r'track/(\d+)', current_song_data["url"])
                    if match:
                        track_id = match.group(1)
                if track_id:
                    current_track_id = track_id
                if first_run:
                    print(f"{now_str} Playing: {current_song} (track id: {track_id})")
                    previous_track_id = current_track_id
                    previous_track_data = copy.deepcopy(current_song_data)
                    first_run = False

                if current_track_id == previous_track_id:
                    if cont_playing >= 120:
                        print(f"{now_str} The current song is the same as the previous one, continuing...")
                        cont_playing = 0
                else:
                    tidalui.pause()  # Pause the current track
                    previous_song_name = previous_track_data['title'] + " - " + previous_track_data['artists']
                    recorder.stop_recording(previous_song_name, previous_track_data['image'],
                                            previous_track_data['artist'],
                                            previous_track_data['title'],
                                            default_album,
                                            clean_art_file)  # Stop recording if the track changes
                    time.sleep(1)
                    print(f"{now_str} Song changed, recording new song...")
                    recorder.start_recording()
                    previous_track_id = current_track_id
                    previous_track_data = copy.deepcopy(current_song_data)
                    tidalui.play()
                    print(f"{now_str} Playing: {current_song} (track id: {current_track_id})")

                    #exit(0)  # Exit the script
            else:
                current_song = " "

            if not current_song:
                print(f"{now_str} songs are currently playing.")
            else:
                pass
        except KeyboardInterrupt:
            print("User interruption. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
    #stop and join the consumer
    task_queue.q.join()
    consumer.stop()
    consumer.join()

if __name__ == "__main__":
    main()
