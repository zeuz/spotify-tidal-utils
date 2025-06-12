# README #

Utils to sync playlist between Spotify and Tidal

### What is this repository for? ###

* daily-mix-sync: A utility to sync Spotify's Daily Mix playlists with Tidal.

* tidal2flac: A utility to convert Tidal playlists to FLAC format.

### How do I get set up? ###

* Install the required dependencies:
  ```bash
  virtualenv venv
  pip install -r requirements.txt
  ```
### Config for daily-mix-sync ###

Fill the config file with your Tidal api token. After the first run you will be redirect to oauth page, then will be stored on db_session_path

### tidal2flac ###
Requirements (just proved on linux):
Tidal HiFi
sox
flac

### config for tidal2flac ###
Tidal HiFi must be enabled with API interface
then  you need to create a device audio loop to capture audio something like this (it depends on what linux flavor you are using):

```bash
alsaloop -C  "plughw:0,0" -P hw:Loopback,0,1 -t 100000 -r 44100 -f S16_LE -c 2
```

you can test it with:
```bash
arecord -D hw:0,1 -f S16_LE -r 44100 -c 2 | lame -r -s 44.1 --bitwidth 16 -m s - test_output.mp3
```

if all is working then check if the Tidal Hifi is working and detecting when a song its changed:
```bash

python3 tidal2flac.py --check
```
you will see the output of the current song and when it changes

After that you can run the script with:
```bash
python3 tidal2flac.py 
```

