import definitions
import mido
import push2_python
import time
import math
import os
import json


class TrackState(object):

    track_num = 0
    has_content = False
    is_playing = False

    def __init__(self, track_num=0):
        self.track_num = track_num


class TrackTriggeringMode(definitions.PyshaMode):

    xor_group = 'pads'

    scene_trigger_buttons = [
        push2_python.constants.BUTTON_1_32T,
        push2_python.constants.BUTTON_1_32,
        push2_python.constants.BUTTON_1_16T,
        push2_python.constants.BUTTON_1_16,
        push2_python.constants.BUTTON_1_8T,
        push2_python.constants.BUTTON_1_8,
        push2_python.constants.BUTTON_1_4T,
        push2_python.constants.BUTTON_1_4
    ]

    pyramidi_channel = 15
    
    track_states = []
    
    pad_pressing_states = {}
    pad_quick_press_time = 0.400

    track_selection_modifier_button_being_pressed = False
    track_selection_modifier_button = push2_python.constants.BUTTON_MASTER

    def initialize(self, settings=None):
        self.pyramidi_channel = self.app.track_selection_mode.pyramidi_channel  # Note TrackSelectionMode needs to have been initialized before TrackTriggeringMode
        self.create_tracks()

    def create_tracks(self):
        for i in range(0, 64):
            self.track_states.append(TrackState(track_num=i))

    def track_is_playing(self, track_num):
        return self.track_states[track_num].is_playing

    def track_has_content(self, track_num):
        return self.track_states[track_num].has_content

    def set_track_is_playing(self, track_num, value, send_to_pyramid=True):
        self.track_states[track_num].is_playing = value
        if send_to_pyramid:
            if value == True:
                self.send_unmute_track(track_num)
            else:
                self.send_mute_track(track_num)

    def set_track_has_content(self, track_num, value):
        self.track_states[track_num].has_content = value

    def set_pyramidi_channel(self, channel, wrap=False):
        self.pyramidi_channel = channel
        if self.pyramidi_channel < 0:
            self.pyramidi_channel = 0 if not wrap else 15
        elif self.pyramidi_channel > 15:
            self.pyramidi_channel = 15 if not wrap else 0

    def pad_ij_to_track_num(self, pad_ij):
        return pad_ij[0] * 8 + pad_ij[1]

    def send_mute_track(self, track_num):
        # Follows pyramidi specification (Pyramid configured to receive on ch 16)
        msg = mido.Message('control_change', control=track_num + 1, value=0, channel=self.pyramidi_channel)
        self.app.send_midi_to_pyramid(msg)

        # Send clip stop in shepherd
        shepherd_track = track_num // 8
        shepherd_clip = track_num % 8
        self.app.shepherd_interface.clip_play_stop(shepherd_track, shepherd_clip)

    def send_unmute_track(self, track_num):
        # Follows pyramidi specification (Pyramid configured to receive on ch 16)
        msg = mido.Message('control_change', control=track_num + 1, value=1, channel=self.pyramidi_channel)
        self.app.send_midi_to_pyramid(msg)

        # Send clip play in shepherd
        shepherd_track = track_num // 8
        shepherd_clip = track_num % 8
        self.app.shepherd_interface.clip_play_stop(shepherd_track, shepherd_clip)

    def activate(self):
        self.pad_pressing_states = {}
        self.track_selection_modifier_button_being_pressed = False
        self.update_buttons()
        self.update_pads()

    def new_track_selected(self):
        self.pad_pressing_states = {}
        self.track_selection_modifier_button_being_pressed = False
        self.app.pads_need_update = True
        self.app.buttons_need_update = True

    def deactivate(self):
        for button_name in self.scene_trigger_buttons:
            self.push.buttons.set_button_color(button_name, definitions.BLACK)
        self.push.buttons.set_button_color(self.track_selection_modifier_button, definitions.BLACK)
        self.app.push.pads.set_all_pads_to_color(color=definitions.BLACK)

    def update_buttons(self):
        for button_name in self.scene_trigger_buttons:
            self.push.buttons.set_button_color(button_name, definitions.WHITE)
        if not self.track_selection_modifier_button_being_pressed:
            self.push.buttons.set_button_color(self.track_selection_modifier_button, definitions.OFF_BTN_COLOR)
        else:
            self.push.buttons.set_button_color(self.track_selection_modifier_button, definitions.BLACK)
            self.push.buttons.set_button_color(self.track_selection_modifier_button, definitions.WHITE, animation=definitions.DEFAULT_ANIMATION)

        # Shepherd buttons
        is_playing, is_recording = self.app.shepherd_interface.get_buttons_state()
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_PLAY, definitions.WHITE if not is_playing else definitions.GREEN)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_STOP, definitions.WHITE if not is_recording else definitions.RED)

    def update_pads(self):
        # Update pads according to track state
        '''
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                track_num = self.pad_ij_to_track_num((i, j))
                track_color = self.app.track_selection_mode.get_track_color(track_num)  # Track color
                cell_color = track_color + '_darker2'  # Choose super darker version of track color
                if self.track_has_content(track_num):
                    cell_color = track_color + '_darker1'  # Choose darker version of track color
                if self.track_is_playing(track_num):
                    cell_color = track_color
                row_colors.append(cell_color)
            color_matrix.append(row_colors)
        self.push.pads.set_pads_color(color_matrix)
        '''
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                state = self.app.shepherd_interface.get_clip_state(i, j)
                cell_color = definitions.WHITE

                if 'p' in state:
                    cell_color = definitions.GREEN

                if 'w' in state or 'W' in state:
                    cell_color = definitions.ORANGE
                
                if 'r' in state:
                    cell_color = definitions.RED 

                if 'c' in state or 'C' in state:
                    cell_color = definitions.YELLOW
                  
                row_colors.append(cell_color)
            color_matrix.append(row_colors)
        self.push.pads.set_pads_color(color_matrix)

    def on_button_pressed(self, button_name):
        if button_name in self.scene_trigger_buttons:
            triggered_scene_row = self.scene_trigger_buttons.index(button_name)
            # Unmute all tracks in that row, mute all tracks from other rows (only tracks that have content)
            for i in range(0, 8):
                for j in range(0, 8):
                    track_num = self.pad_ij_to_track_num((i, j))
                    # If track in selected row  
                    # # TODO: check that indexing is correct
                    if i == triggered_scene_row:
                        if self.track_has_content(track_num):
                            self.set_track_is_playing(track_num, True)
                    else:
                        if self.track_has_content(track_num):
                            self.set_track_is_playing(track_num, False)
            self.app.pads_need_update = True

            return True  # Prevent other modes to get this event

        elif button_name == self.track_selection_modifier_button:
            self.track_selection_modifier_button_being_pressed = True
            return True  # Prevent other modes to get this event

        # Shepherd play/stop
        if button_name == push2_python.constants.BUTTON_PLAY:
            self.app.shepherd_interface.global_play()
            return True # Prevent other modes to get this event
        elif button_name == push2_python.constants.BUTTON_PLAY:
            self.app.shepherd_interface.global_stop()
            return True  # Prevent other modes to get this event

    def on_button_released(self, button_name):
        if button_name == self.track_selection_modifier_button:
            self.track_selection_modifier_button_being_pressed = False
            return True  # Prevent other modes to get this event

    def on_encoder_rotated(self, encoder_name, increment):
        if encoder_name == push2_python.constants.ENCODER_TEMPO_ENCODER:
            new_bpm = int(self.app.shepherd_interface.get_bpm()) + increment
            self.app.shepherd_interface.set_bpm(new_bpm)
            return True  # Prevent other modes to get this event

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        if not self.track_selection_modifier_button_being_pressed:
            self.pad_pressing_states[pad_n] = time.time()  # Store time at which pad_n was pressed
            self.push.pads.set_pad_color(pad_ij, color=definitions.GREEN)
            return True  # Prevent other modes to get this event
        else:
            # If a pad is pressed while the modifier key is also pressed,
            # we select the corresponding track. This will trigger exiting
            # the PyramidTrackTriggering mode
            track_num = self.pad_ij_to_track_num(pad_ij)
            self.app.track_selection_mode.select_track(track_num)
            return True  # Prevent other modes to get this event

    def on_pad_released(self, pad_n, pad_ij, velocity):
        pressing_time = self.pad_pressing_states.get(pad_n, None)
        is_long_press = False
        if pressing_time is None:
            # Consider quick press (this should not happen as self.pad_pressing_states[pad_n] should have been set before)
            pass
        else:
            if time.time() - pressing_time > self.pad_quick_press_time:
                # Consider this is a long press
                is_long_press = True
            self.pad_pressing_states[pad_n] = None  # Reset pressing time to none

        track_num = self.pad_ij_to_track_num(pad_ij)

        if is_long_press:
            # Long press
            #   - if track has no content: mark it as having content
            #   - if track has content: mark it as having no content
            self.set_track_has_content(track_num, not self.track_has_content(track_num))
            if self.track_is_playing(track_num):
                self.set_track_is_playing(track_num, False)

        else:
            # Short press
            #   - if track has no content: mark it as having content
            #   - if track has content: toggle mute/unmute
            if not self.track_has_content(track_num):
                self.set_track_has_content(track_num, True)
            else:
                if self.track_is_playing(track_num):
                    self.set_track_is_playing(track_num, False)
                else:
                    self.set_track_is_playing(track_num, True)
        
        self.app.pads_need_update = True
        return True  # Prevent other modes to get this event
