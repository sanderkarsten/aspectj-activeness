import configparser
import os
import requests
import time
import progressbar
from pprint import pprint

# Read the api token from a config.ini file and store it as header for requests
config = configparser.ConfigParser()
config.read('config.ini')
token = os.getenv('GITHUB_TOKEN', config.get('auth', 'token'))
headers = {'Authorization': f'token {token}', "Accept": "application/vnd.github.mercy-preview+json"}


class URLResource:
    def __init__(self, url, type):
        self.default_url = url
        self.current_url = url
        self.type = type
        self.rate_limit = "https://api.github.com/rate_limit"

    def get(self, params=None):
        remaining_searches = requests.get(self.rate_limit).json()["resources"][self.type]["remaining"]
        if remaining_searches == 0:
            time.sleep(10)
            self.get(params)
        response = requests.get(self.current_url, headers=headers, params=params)
        # Raise exception for a non 200 status code
        try:
            response.raise_for_status()
        except Exception:
            print("Rate limit exceeded sleeping 1 minute")
            time.sleep(60)
            response = requests.get(self.current_url, headers=headers, params=params)
            response.raise_for_status()
        return response

    def get_multiple_pages(self, params=None):
        print("Fetching multiple pages")
        response = self.get(params)
        self.__init_progress_bar(response)
        result = list(response.json()["items"])
        i = 0
        while "next" in response.links:
            self.current_url = response.links["next"]["url"]
            self.__update_progress_bar(response, i)
            response = self.get(params)
            result = result + list(response.json()["items"])
            i = i+1
        self.current_url = self.default_url
        self.bar.finish()
        print("Completed fetching")
        return result

    def __init_progress_bar(self, response):
        if "total_count" in response.json():
            self.bar = progressbar.ProgressBar(maxval=response.json()["total_count"],
                                               widgets=[progressbar.Bar('=', '[', ']'), ' ',
                                                        progressbar.SimpleProgress()]
                                               )
            self.bar.start()

    def __update_progress_bar(self, response, i):
        if "total_count" in response.json():
            total = response.json()["total_count"]
            self.bar.update(100 * i if total - 100 * i >= 0 else total)
