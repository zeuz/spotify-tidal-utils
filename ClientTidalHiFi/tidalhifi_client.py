import requests


class TidalHiFiClient:
    def __init__(self, srv_url):
        self.srv_url = srv_url

    def get_current_song_data(self):
        try:
            response = requests.get(f"{self.srv_url}/current")
            response.raise_for_status()
            data = response.json()

            if data:
                return data
            else:
                return None
        except requests.RequestException as e:
            print(f"Error getting current song: {e}")
            return None

    def play(self):
        try:
            response = requests.get(f"{self.srv_url}/play")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Play error: {e}")
            return False

    def pause(self):
        try:
            response = requests.get(f"{self.srv_url}/pause")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Pause error: {e}")
            return False
