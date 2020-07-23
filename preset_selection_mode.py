import definitions
import mido
import push2_python
import time
import os
import json


class PresetSelectionMode(definitions.PyshaMode):

    xor_group = 'pads'
    
    favourtie_presets = {}
    favourtie_presets_filename = 'favourite_presets.json'
    pad_pressing_states = {}
    pad_quick_press_time = 0.400

    def initialize(self, settings=None):
        if os.path.exists(self.favourtie_presets_filename):
            self.favourtie_presets = json.load(open(favourtie_presets))
    
    def add_favourite_preset(self, preset_number, bank_number=0):
        instrument_short_name = self.app.track_selection_mode.get_current_track_instrument_short_name(track_num) 
        if instrument_short_name not in self.favourtie_presets:
            self.favourtie_presets[instrument_short_name] = []
        self.favourtie_presets[instrument_short_name].append((preset_number, bank_number))
        json.dump(self.favourtie_presets, open(self.favourtie_presets_filename, 'w'))  # Save to file

    def remove_favourite_preset(self, preset_number, bank_number=0):
        instrument_short_name = self.app.track_selection_mode.get_current_track_instrument_short_name(track_num) 
        if instrument_short_name in self.favourtie_presets:
            self.favourtie_presets[instrument_short_name] = \
                [(fp_preset_number, fp_bank_number) for fp_preset_number, fp_bank_number in self.favourtie_presets[instrument_short_name] 
                if preset_number == c_preset_number and bank_number == fp_bank_number]
            json.dump(self.favourtie_presets, open(self.favourtie_presets_filename, 'w'))  # Save to file

    def preset_num_in_favourites(self, preset_number, bank_number=0):
        instrument_short_name = self.app.track_selection_mode.get_current_track_instrument_short_name(track_num) 
        for fp_preset_number, fp_bank_number in self.favourtie_presets[instrument_short_name]:
            if preset_number == c_preset_number and bank_number == fp_bank_number:
                return True
        return False

    def pad_ij_to_preset_num(self, pad_ij):
        return pad_ij[0] * 8 + pad_ij[1]  # TODO: test if indexes should be reversed?

    def send_select_new_preset(self, preset_num):
        msg = mido.Message('program_change', program=preset_num)
        self.app.send_midi(msg)

    def send_select_new_bank(self, bank_num):
        # TODO: this is currently unused, also we should find the correct bytes for bank change
        #msg = mido.Message('program_change', program=bank_num)
        #self.app.send_midi(msg)
        pass

    def activate(self):
        self.update_pads()

    def deactivate(self):
        app.push.pads.set_all_pads_to_color(color=definitions.BLACK)

    def update_pads(self):
        instrument_short_name = self.app.track_selection_mode.get_current_track_instrument_short_name(track_num) 
        track_color = self.app.track_selection_mode.get_track_color(track_num) 
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                preset_num = self.pad_ij_to_preset_num((i, j))
                cell_color = track_color
                if not self.preset_num_in_favourites(preset_num):
                    cell_color = f'{cell_color}_darker1'  # If preset not in favourites, use a darker version of the track color
                row_colors.append(cell_color)
            color_matrix.append(row_colors)
        self.push.pads.set_pads_color(color_matrix)

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        pad_pressing_states[pad_n] = time.time()  # Store time at which pad_n was pressed
        return True  # Prevent other modes to get this event

    def on_pad_released(self, pad_n, pad_ij, velocity):
        pressing_time = pad_pressing_states.get(pad_n, None)
        is_long_press = False
        if pressing_time is None:
            # Consider quick press (this should not happen as pad_pressing_states[pad_n] should have been set before)
            pass
        else:
            if time.time() - pressing_time > self.pad_quick_press_time:
                # Consider this is a long press
                is_long_press = True
            pad_pressing_states[pad_n] = None  # Reset pressing time to none

        preset_num = self.pad_ij_to_preset_num((i, j))

        if is_long_press:
            # Add preset to favourites, don't send any MIDI
            self.add_favourite_preset(preset_num)  # TODO: handle banks/pages here       
            self.app.pads_need_update = True

        else:
            # Send midi message to select the preset
            self.send_select_new_preset(preset_num)
            # TODO: send bank information as well once banks/pages are handled

        return True  # Prevent other modes to get this event
