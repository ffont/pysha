from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
import threading
import asyncio

osc_send_host = "127.0.0.1"
osc_send_port = 9003
osc_receive_port = 9004

'''
def received_state(values):
    print(values)


class OSCReceiverThread(threading.Thread):
    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        osc = OSCThreadServer()
        sock = osc.listen(address='0.0.0.0', port=osc_receive_port, default=True)
        osc.bind(b'/stateFromShepherd', received_state)
'''

class ShepherdInterface(object):

    osc_sender = None

    def __init__(self):
        self.osc_sender = OSCClient(osc_send_host, osc_send_port, encoding='utf8')

    def run_get_state_transport_thread():
        self.osc_sendersend_message('/state/transport')
        pass

    def run_get_state_tracks_thread():
        self.osc_sendersend_message('/state/tracks')
        pass

    def receive_state_from_shepherd(msg):
        # TODO: store tracks state. if changed sett app update buttons needed
        print(msg)
    
    def track_select(self, track_number):
        pass

    def clip_play_stop(self, track_number, clip_number):
        pass

    def global_play(self):
        pass

    def global_record(self):
        pass

    def get_clip_state(self, track_num, clip_num):
        pass

    def get_buttons_state(self):
        is_playing = True
        is_recording = False
        return is_playing, is_recording

    def get_bpm(self):
        return 120

    def set_bpm(self, bpm):
        pass

