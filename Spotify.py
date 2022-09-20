import numpy as np
import requests
import base64 as b64
import datetime
from urllib.parse import urlencode
import http.server
import socketserver
import threading
from threading import Lock
import webbrowser
import sys
import os
import json
import time
import urllib3


class Spotify_API:
    
    #Server
    timeout = False
    tShutDown = datetime.timedelta(seconds=1)
    tstartUp = 0

    #Client Details
    Client_ID = ""
    Client_Secret = ""
    Client_Details_e = ""

    #Endpoints
    redirect_uri = 'https://aa2aa.pythonanywhere.com/Spotify.html'
    authorise_url = "https://accounts.spotify.com/authorize?"
    token_url = "https://accounts.spotify.com/api/token"

    #Authentification
    Auth_granted = False
    Authorization_Code = ""

    #Access
    Access_Token = "" 
    Refresh_Token = ""
    Timeout = 0
    did_expire = False

    #Transfer playback
    Device_IDs = []

    #Current Track
    Current_Track_Image_url = ""
    Current_Track = ""
    Current_Track_duration = 0
    Current_Track_position = 0
    Current_Track_ID = ""
    current_Device={}

    #user playlists
    Playlists = []
    Songf = []

    mutex = Lock()

    def __init__(self):

        #Client Details
        self.Client_ID = "efaf7fb1b79b4aba9fbe85f227615f4b"
        self.Client_Secret = "53276fb8e44f45549dd3cec05f2fb854"

        #Decode client details
        Client_Details = f"{self.Client_ID}:{self.Client_Secret}"
        self.Client_Details_e = b64.b64encode(Client_Details.encode()).decode()

        #start up time
        self.tstartUp = datetime.datetime.now()
        

    def start_server_cmd(self):
        os.system('python Server.py')

    #Start Server function
    def start_server(self):
        
        PORT = 8080
        Server = http.server.SimpleHTTPRequestHandler
        
        with open("logfile.txt","w") as files:
            files.write("")

        with socketserver.TCPServer(("",PORT), Server) as httpd:
            print("serving as port", PORT)

            buffer = 1

            sys.stderr = open("logfile.txt", "w", buffer)
            
            now = datetime.datetime.now()

            print(f"{now} : {self.tstartUp+self.tShutDown}")

            while now < (self.tstartUp + self.tShutDown):
                print("server_active")
                
                httpd.handle_request()

                now = datetime.datetime.now()
                
            print("Server Shutdown")

    #Get Authorisation 
    def get_Authorization(self):
        
        if self.Auth_granted == False:
      
            scopes = "user-modify-playback-state user-read-playback-state user-read-currently-playing user-read-recently-played playlist-read-collaborative playlist-read-private playlist-modify-private streaming user-library-read user-library-modify"
            
            Authorization_Data= {
                "response_type": 'code',
                "client_id":self.Client_ID,
                "scope":scopes,
                "redirect_uri": self.redirect_uri,
            }

            r = requests.get(self.authorise_url+urlencode(Authorization_Data))

            print(r.url)

            webbrowser.open(r.url)
            
            g = requests.get('https://aa2aa.pythonanywhere.com/code')

            while(g.json()['code']==''):
                time.sleep(2)
                g=requests.get('https://aa2aa.pythonanywhere.com/code')

            self.Authorization_Code = g.json()['code']
            
            print("Authorization Code: "+f"{self.Authorization_Code}")
            
            self.Auth_granted = True

            return True
        
            
    #Get Access Token
    def get_AccessToken(self):

        AccessToken_Data= {
            "grant_type":"authorization_code",
            "code":self.Authorization_Code,
            "redirect_uri":self.redirect_uri
        }
        
        AccessToken_Header= {
            "Authorization": "Basic "+self.Client_Details_e,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        r = requests.post(self.token_url, data=urlencode(AccessToken_Data), headers=AccessToken_Header)
        
        #print(r,"\n")

        #print("\n"+f"{r.json()['access_token']}   {r.json()['expires_in']}")

        now = datetime.datetime.now()

        
        self.Access_Token = r.json()['access_token']
        self.Refresh_Token = r.json()['refresh_token']
        self.Timeout = now + datetime.timedelta(seconds=r.json()['expires_in'])

        self.did_expire = self.Timeout < now
        


    def refresh_token(self):
        now = datetime.datetime.now()

        if self.Timeout < now:
            self.did_expire = True

            AccessToken_Data= {
                "grant_type":"refresh_token",
                "refresh_token":self.Refresh_Token
            }
            
            AccessToken_Header= {
                "Authorization": "Basic "+self.Client_Details_e,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            r = requests.post(self.token_url, data=urlencode(AccessToken_Data), headers=AccessToken_Header)

            now = datetime.datetime.now()

            self.Access_Token = r.json()['access_token']
            self.Timeout = now + datetime.timedelta(seconds=r.json()['expires_in'])

            self.did_expire = self.Timeout < now
        
        else:
            pass

    def get_User_Playlists(self, offset):

        endpoint = f"https://api.spotify.com/v1/me/playlists?limit=50&offset={offset}"

        get_Playlists_Header = {
            'Content-Type':'application/json',
            'Authorization':f"Bearer {self.Access_Token}",
            
        }

        r = requests.get(endpoint, headers=get_Playlists_Header)

        r.encoding = 'utf-8'

        g = r.json()

        print(len(g))

        for key, value in g.items():

            if(key=='items'):
                for a in value:
                    
                    self.Playlists.append({"name":a['name'], "image":a['images'][0]['url'], "tracks":a['tracks']['href']})

    def get_tracks(self, playlist_endpoint):

        get_Tracks_Header = {
            'Content-Type':'application/json',
            'Authorization':f"Bearer {self.Access_Token}",
        }

        r = requests.get(playlist_endpoint, headers=get_Tracks_Header)

        print("\n")
        g = r.json()

        song = {"name":"", "acousticness":0, "danceability":0, "energy":0, "instrumentalness":0, "key":0, "liveness":0, "loudness":0, "mode":0, "speechiness":0, "tempo":0, "valence":0 }

        endpoint = "https://api.spotify.com/v1/audio-features/"

        for key, value in g.items():
            if key == 'items':
                for a in value:
                    

                    link = endpoint + f"{a['track']['id']}"

                    r = requests.get(link, headers=get_Tracks_Header)

                    try:
                        song["name"] = a['track']['name']
                        song['acousticness'] = r.json()['acousticness']
                        song['danceability'] = r.json()['danceability']
                        song['energy'] = r.json()['energy']
                        song['instrumentalness'] = r.json()['instrumentalness']
                        song['key'] = r.json()['key']
                        song['liveness'] = r.json()['liveness']
                        song['loudness'] = r.json()['loudness']
                        song['mode'] = r.json()['mode']
                        song['speechiness'] = r.json()['speechiness']
                        song['tempo'] = r.json()['tempo']
                        song['valence'] = r.json()['valence']

                        self.Songf.append(song)
                    except:
                        pass

                    self.Songf = [dict(t) for t in {tuple(d.items()) for d in self.Songf}]
                    
                    
        
        
    def get_Device_Names(self):

        self.Device_IDs = []

        self.refresh_token()
        
        #Find available devices
        endpoint = "https://api.spotify.com/v1/me/player/devices"

        Available_Devices_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.get(endpoint, headers=Available_Devices_Header)
            
        for i in r.json()['devices']:   
            if(i['is_restricted'] == False):
                self.Device_IDs.append({i['name']:i['id']})
            if(i['is_active']==True):
                self.current_Device = {i['name']:i['id']}


    def transfer_playback(self, device_code):

        self.refresh_token()

        Available_Devices_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        #Transfer playback
        endpoint = "https://api.spotify.com/v1/me/player"

        Transfer_Playback_Data = {
            'device_ids':[device_code]
        }

        r = requests.put(endpoint, data=json.dumps(Transfer_Playback_Data) ,headers=Available_Devices_Header)

    def get_current_track(self):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/currently-playing"

        current_track_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.get(endpoint, headers=current_track_Header)

        try:
            self.Current_Track_Image_url = r.json()['item']['album']['images'][1]['url']
            self.Current_Track = r.json()['item']['name']
            self.Current_Track_duration = r.json()['item']['duration_ms']
            self.Current_Track_position = r.json()['progress_ms']
            self.Current_Track_ID = r.json()['item']['id']

        except:
            self.Current_Track_Image_url = "https://www.wrapitup.co.uk/wp-content/uploads/2019/05/AmericanWrapx-640px.jpg"
            self.Current_Track = "Not playing anything"
            self.Current_Track_duration = 10
            self.Current_Track_position = 0
            self.Current_Track_ID = 0

    def pause_playback(self):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/pause"

        pause_playback_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.put(endpoint, headers=pause_playback_Header)

    def play_playback(self):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/play"

        play_playback_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.put(endpoint, headers=play_playback_Header)

    def skip_playback(self):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/next"

        skip_playback_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.post(endpoint, headers=skip_playback_Header)

    def prev_playback(self):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/previous"

        prev_playback_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }

        r = requests.post(endpoint, headers=prev_playback_Header)

    def Seek_position(self, pos=0):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/seek"

        seek_pos_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }
    
        seek_pos_Data = {
            'position_ms':pos
        }

        r = requests.put(endpoint, params=seek_pos_Data ,headers=seek_pos_Header)

    def repeat_song(self):
        self.Seek_position()

    def Set_Volume(self, vol=5):

        self.refresh_token()

        endpoint = "https://api.spotify.com/v1/me/player/volume"

        set_vol_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }
    
        set_vol_Data = {
            'volume_percent':vol
        }

        r = requests.put(endpoint, params=set_vol_Data ,headers=set_vol_Header)

    def add_to_playlist(self):

        self.refresh_token()

        playlist_id = "6dtFCy85SlEdvLVIPemsTn"

        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        add_playlist_Header = {
            'Authorization':f"Bearer {self.Access_Token}",
            'Content-Type':'application/json'
        }
    
        datas = {
            "uris":[f"spotify:track:{self.Current_Track_ID}"]
        }

        r = requests.post(endpoint, params=datas, headers=add_playlist_Header)
        
        print(r.json())
