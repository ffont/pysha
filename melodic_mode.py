import definitions
import mido
import push2_python.constants
import time


class MelodicMode(definitions.PyshaMode):

    notes_being_played = []
    root_midi_note = 0  # default redefined in initialize
    scale_pattern = [True, False, True, False, True, True, False, True, False, True, False, True]
    fixed_velocity_mode = False
    use_poly_at = False  # default redefined in initialize
    channel_at_range_start = 401  # default redefined in initialize
    channel_at_range_end = 800 # default redefined in initialize
    poly_at_max_range = 40 # default redefined in initialize
    poly_at_curve_bending = 50  # default redefined in initialize
    latest_channel_at_value = (0, 0)
    latest_poly_at_value = (0, 0)
    latest_velocity_value = (0, 0)
    last_time_at_params_edited = None

    def initialize(self, settings=None):
        if settings is not None:
            self.use_poly_at = settings.get('use_poly_at', True)
            self.set_root_midi_note(settings.get('root_midi_note', 64))
            self.channel_at_range_start = settings.get('channel_at_range_start', 401)
            self.channel_at_range_end = settings.get('channel_at_range_end', 800)
            self.poly_at_max_range = settings.get('poly_at_max_range', 40)
            self.poly_at_curve_bending = settings.get('poly_at_curve_bending', 50)

    def get_settings_to_save(self):
        return {
            'use_poly_at': self.use_poly_at,
            'root_midi_note': self.root_midi_note,
            'channel_at_range_start': self.channel_at_range_start,
            'channel_at_range_end': self.channel_at_range_end,
            'poly_at_max_range': self.poly_at_max_range,
            'poly_at_curve_bending': self.poly_at_curve_bending,
        }

    def set_channel_at_range_start(self, value):
        # Parameter in range [401, channel_at_range_end - 1]
        if value < 401:
            value = 401
        elif value >= self.channel_at_range_end:
            value = self.channel_at_range_end - 1
        self.channel_at_range_start = value
        self.last_time_at_params_edited = time.time()

    def set_channel_at_range_end(self, value):
        # Parameter in range [channel_at_range_start + 1, 2000]
        if value <= self.channel_at_range_start:
            value = self.channel_at_range_start + 1
        elif value > 2000:
            value = 2000
        self.channel_at_range_end = value
        self.last_time_at_params_edited = time.time()

    def set_poly_at_max_range(self, value):
        # Parameter in range [0, 127]
        if value < 0:
            value = 0
        elif value > 127:
            value = 127
        self.poly_at_max_range = value
        self.last_time_at_params_edited = time.time()

    def set_poly_at_curve_bending(self, value):
        # Parameter in range [0, 100]
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self.poly_at_curve_bending = value
        self.last_time_at_params_edited = time.time()

    def get_poly_at_curve(self):
        pow_curve = [pow(e, 3*self.poly_at_curve_bending/100) for e in [i/self.poly_at_max_range for i in range(0, self.poly_at_max_range)]]
        return [int(127 * pow_curve[i]) if i < self.poly_at_max_range else 127 for i in range(0, 128)]

    def add_note_being_played(self, midi_note, source):
        self.notes_being_played.append({'note': midi_note, 'source': source})

    def remove_note_being_played(self, midi_note, source):
        self.notes_being_played = [note for note in self.notes_being_played if note['note'] != midi_note or note['source'] != source]

    def remove_all_notes_being_played(self):
        self.notes_being_played = []

    def pad_ij_to_midi_note(self, pad_ij):
        return self.root_midi_note + ((7 - pad_ij[0]) * 5 + pad_ij[1])

    def is_midi_note_root_octave(self, midi_note):
        relative_midi_note = (midi_note - self.root_midi_note) % 12
        return relative_midi_note == 0

    def is_black_key_midi_note(self, midi_note):
        relative_midi_note = (midi_note - self.root_midi_note) % 12
        return not self.scale_pattern[relative_midi_note]

    def is_midi_note_being_played(self, midi_note):
        for note in self.notes_being_played:
            if note['note'] == midi_note:
                return True
        return False

    def note_number_to_name(self, note_number):
        semis = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_number = int(round(note_number))
        return semis[note_number % 12] + str(note_number//12 - 1)

    def set_root_midi_note(self, note_number):
        self.root_midi_note = note_number
        if self.root_midi_note < 0:
            self.root_midi_note = 0
        elif self.root_midi_note > 127:
            self.root_midi_note = 127

    def activate(self):
        if self.use_poly_at:
            self.push.pads.set_polyphonic_aftertouch()
        else:
            self.push.pads.set_channel_aftertouch()

        # Configure polyAT and AT
        self.push.pads.set_channel_aftertouch_range(range_start=self.channel_at_range_start, range_end=self.channel_at_range_end)
        self.push.pads.set_velocity_curve(velocities=self.get_poly_at_curve())

        self.update_buttons()

    def deactivate(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, definitions.BLACK)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, definitions.BLACK)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, definitions.BLACK)

    def check_for_delayed_actions(self):
        if self.last_time_at_params_edited is not None and time.time() - self.last_time_at_params_edited > definitions.DELAYED_ACTIONS_APPLY_TIME:
            # Update channel and poly AT parameters
            self.push.pads.set_channel_aftertouch_range(range_start=self.channel_at_range_start, range_end=self.channel_at_range_end)
            self.push.pads.set_velocity_curve(velocities=self.get_poly_at_curve())
            self.last_time_at_params_edited = None

    def on_midi_in(self, msg):
        # Update the list of notes being currently played so push2 pads can be updated accordingly
        if msg.type == "note_on":
            if msg.velocity == 0:
                self.remove_note_being_played(msg.note, self.app.midi_in.name)
            else:
                self.add_note_being_played(msg.note, self.app.midi_in.name)
        elif msg.type == "note_off":
            self.remove_note_being_played(msg.note, self.app.midi_in.name)
        self.app.pads_need_update = True 

    def update_accent_button(self):
        # Accent button has its own method so it can be reused in the rhythmic mode which inherits from melodic mode
        if self.fixed_velocity_mode:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, definitions.WHITE, animation='pulsing')
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, definitions.OFF_BTN_COLOR)

    def update_buttons(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, definitions.WHITE)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, definitions.WHITE)
        self.update_accent_button()

    def update_pads(self):
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                corresponding_midi_note = self.pad_ij_to_midi_note([i, j])
                cell_color = definitions.WHITE
                if self.is_black_key_midi_note(corresponding_midi_note):
                    cell_color = definitions.BLACK
                if self.is_midi_note_root_octave(corresponding_midi_note):
                    try:
                        cell_color = self.app.pyramidi_mode.get_current_track_color()
                    except AttributeError:
                        cell_color = definitions.YELLOW
                if self.is_midi_note_being_played(corresponding_midi_note):
                    cell_color = definitions.NOTE_ON_COLOR

                row_colors.append(cell_color)
            color_matrix.append(row_colors)

        self.push.pads.set_pads_color(color_matrix)

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        if midi_note is not None:
            self.latest_velocity_value = (time.time(), velocity)
            self.add_note_being_played(midi_note, 'push')
            msg = mido.Message('note_on', note=midi_note, velocity=velocity if not self.fixed_velocity_mode else 127)
            self.app.send_midi(msg)
            self.update_pads()  # Directly calling update pads method because we want user to feel feedback as quick as possible

    def on_pad_released(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        if midi_note is not None:
            self.remove_note_being_played(midi_note, 'push')
            msg = mido.Message('note_off', note=midi_note, velocity=velocity)
            self.app.send_midi(msg)
            self.update_pads()  # Directly calling update pads method because we want user to feel feedback as quick as possible

    def on_pad_aftertouch(self, pad_n, pad_ij, velocity):
        if pad_n is not None:
            # polyAT mode
            self.latest_poly_at_value = (time.time(), velocity)
            midi_note = self.pad_ij_to_midi_note(pad_ij)
            if midi_note is not None:
                msg = mido.Message('polytouch', note=midi_note, value=velocity)
        else:
            # channel AT mode
            self.latest_channel_at_value = (time.time(), velocity)
            msg = mido.Message('aftertouch', value=velocity)
        self.app.send_midi(msg)

    def on_touchstrip(self, value):
        msg = mido.Message('pitchwheel', pitch=value)
        self.app.send_midi(msg)

    def on_sustain_pedal(self, sustain_on):
        msg = mido.Message('control_change', control=64, value=127 if sustain_on else 0)
        self.app.send_midi(msg)

    def on_button_pressed(self, button_name):
        if button_name == push2_python.constants.BUTTON_OCTAVE_UP:
            self.set_root_midi_note(self.root_midi_note + 12)
            self.app.pads_need_update = True

        elif button_name == push2_python.constants.BUTTON_OCTAVE_DOWN:
            self.set_root_midi_note(self.root_midi_note - 12)
            self.app.pads_need_update = True

        elif button_name == push2_python.constants.BUTTON_ACCENT:
            self.fixed_velocity_mode = not self.fixed_velocity_mode
            self.app.buttons_need_update = True
            self.app.pads_need_update = True
