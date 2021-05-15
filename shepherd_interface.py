from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
import threading
import asyncio
import time

osc_send_host = "127.0.0.1"
osc_send_port = 9003
osc_receive_port = 9004

tracks_state_fps = 4.0
transport_state_fps = 10.0

class ShepherdInterface(object):

    app = None

    osc_sender = None
    osc_server = None

    state_transport_check_thread = None
    state_tracks_check_thread = None

    last_received_tracks_raw_state = ""
    parsed_state = {}

    def __init__(self, app):
        self.app = app

        self.osc_sender = OSCClient(osc_send_host, osc_send_port, encoding='utf8')

        self.osc_server = OSCThreadServer()
        sock = self.osc_server.listen(address='0.0.0.0', port=osc_receive_port, default=True)
        self.osc_server.bind(b'/stateFromShepherd', self.receive_state_from_shepherd)

        self.run_get_state_transport_thread()
        self.run_get_state_tracks_thread()

    def run_get_state_transport_thread(self):
        self.state_transport_check_thread = threading.Thread(target=self.check_transport_state)        
        self.state_transport_check_thread.start()

    def run_get_state_tracks_thread(self):
        self.state_tracks_check_thread = threading.Thread(target=self.check_tracks_state)        
        self.state_tracks_check_thread.start()

    def check_transport_state(self):
        while True:
            time.sleep(1.0/transport_state_fps)
            self.osc_sender.send_message('/state/transport', [])

    def check_tracks_state(self):
        while True:
            time.sleep(1.0/tracks_state_fps)
            self.osc_sender.send_message('/state/tracks', [])

    def receive_state_from_shepherd(self, values):
        
        state = values.decode("utf-8")
        if state.startswith("transport"):
            parts = state.split(',')
            old_is_playing = self.parsed_state.get('isPlaying', False)
            old_is_recording = self.parsed_state.get('isRecording', False)
            self.parsed_state['isPlaying'] = parts[1] == "p"
            if 'clips' in self.parsed_state:
                is_recording = False
                for track_clips in self.parsed_state['clips']:
                    for clip in track_clips:
                        if 'r' in clip or 'w' in clip or 'W' in clip:
                            is_recording = True
                            break
                self.parsed_state['isRecording'] = is_recording
            else:
                self.parsed_state['isRecording'] = False
            self.parsed_state['bpm'] = parts[2]
            self.parsed_state['playhead'] = parts[3]
            
            if old_is_playing != self.parsed_state['isPlaying'] or old_is_recording != self.parsed_state['isRecording']:
                self.app.buttons_need_update = True

        elif state.startswith("tracks"):
            if state != self.last_received_tracks_raw_state:
                parts = state.split(',')
                track_clips_state = []
                current_track_clips_state = []
                in_track = False
                for part in parts:
                    if part == "t":
                        in_track = True
                        if current_track_clips_state:
                            track_clips_state.append(current_track_clips_state[1:])  # Remove first element which is # clips per track)
                        current_track_clips_state = []
                    else:
                        if in_track:
                            current_track_clips_state.append(part)

                self.parsed_state['clips'] = track_clips_state
                self.app.pads_need_update = True
                self.last_received_tracks_raw_state = state
    
    def track_select(self, track_number):
        self.osc_sender.send_message('/track/select', [track_number])

    def clip_play_stop(self, track_number, clip_number):
        self.osc_sender.send_message('/clip/playStop', [track_number, clip_number])

    def get_clip_state(self, track_num, clip_num):
        if self.parsed_state['clips']:
            return self.parsed_state['clips'][track_num][clip_num]
        else:
            return 'sn'

    def global_play(self):
        self.osc_sender.send_message('/transport/playStop', [])

    def global_record(self):
        self.osc_sender.send_message('/transport/recordOnOff', [])

    def get_buttons_state(self):
        is_playing = self.parsed_state.get('isPlaying', False)
        is_recording = self.parsed_state.get('isRecording', False)
        return is_playing, is_recording

    def get_bpm(self):
        return self.parsed_state.get('bpm', 120)

    def set_bpm(self, bpm):
        self.osc_sender.send_message('/transport/setBpm', [float(bpm)])

