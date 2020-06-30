import definitions
import mido
import push2_python
import time
import math

from definitions import PyshaMode, OFF_BTN_COLOR, LAYOUT_MELODIC, LAYOUT_RHYTHMIC, PYRAMIDI_CHANNEL
from display_utils import draw_text_at, show_title, show_value, show_text


class PyramidiMode(PyshaMode):

    tracks_info = []
    pyramid_track_button_names_a = [
        push2_python.constants.BUTTON_LOWER_ROW_1,
        push2_python.constants.BUTTON_LOWER_ROW_2,
        push2_python.constants.BUTTON_LOWER_ROW_3,
        push2_python.constants.BUTTON_LOWER_ROW_4,
        push2_python.constants.BUTTON_LOWER_ROW_5,
        push2_python.constants.BUTTON_LOWER_ROW_6,
        push2_python.constants.BUTTON_LOWER_ROW_7,
        push2_python.constants.BUTTON_LOWER_ROW_8
    ]
    pyramid_track_button_names_b = [
        push2_python.constants.BUTTON_1_32T,
        push2_python.constants.BUTTON_1_32,
        push2_python.constants.BUTTON_1_16T,
        push2_python.constants.BUTTON_1_16,
        push2_python.constants.BUTTON_1_8T,
        push2_python.constants.BUTTON_1_8,
        push2_python.constants.BUTTON_1_4T,
        push2_python.constants.BUTTON_1_4
    ]
    pyramid_track_selection_button_a = False
    pyramid_track_selection_button_a_pressing_time = 0
    selected_pyramid_track = 0
    pyramid_track_selection_quick_press_time = 0.400
    pyramidi_channel = PYRAMIDI_CHANNEL


    def initialize(self, settings=None):
        
        for i in range(0, 64):
            data = {
                'track_name': '{0}{1}'.format((i % 16) + 1, ['A', 'B', 'C', 'D'][i//16]),
                'instrument_name': '-',
                'instrument_short_name': '-',
                'color': definitions.GRAY_DARK,
                'default_layout': LAYOUT_MELODIC,
            }
            if i % 8 == 0:
                data['instrument_name'] = 'Deckard\'s Dream'
                data['instrument_short_name'] = 'DDRM'
                data['color'] = definitions.ORANGE
            elif i % 8 == 1:
                data['instrument_name'] = 'Minitaur'
                data['instrument_short_name'] = 'MINITAUR'
                data['color'] = definitions.YELLOW
            elif i % 8 == 2:
                data['instrument_name'] = 'Dominion'
                data['instrument_short_name'] = 'DOMINON'
                data['color'] = definitions.TURQUOISE
            elif i % 8 == 3:
                data['instrument_name'] = 'Kijimi'
                data['instrument_short_name'] = 'KIJIMI'
                data['color'] = definitions.LIME
            elif i % 8 == 4:
                data['instrument_name'] = 'Black Box (Pads)'
                data['instrument_short_name'] = 'BBPADS'
                data['color'] = definitions.RED
                data['default_layout'] = LAYOUT_RHYTHMIC
            elif i % 8 == 5:
                data['instrument_name'] = 'Black Box (Notes)'
                data['instrument_short_name'] = 'BBNOTES'
                data['color'] = definitions.PINK
            self.tracks_info.append(data)

    def get_all_distinct_instrument_short_names(self):
        return list(set([track['instrument_short_name'] for track in self.tracks_info]))

    def get_current_track_instrument_short_name(self):
        return self.tracks_info[self.selected_pyramid_track]['instrument_short_name']

    def get_current_track_color(self):
        return self.tracks_info[self.selected_pyramid_track]['color']

    def get_current_track_color_rgb(self):
        return definitions.get_color_rgb_float(self.get_current_track_color())
        
    def load_current_default_layout(self):
        if self.tracks_info[self.selected_pyramid_track]['default_layout'] == LAYOUT_MELODIC:
            self.app.set_melodic_mode()
        elif self.tracks_info[self.selected_pyramid_track]['default_layout'] == LAYOUT_RHYTHMIC:
            self.app.set_rhythmic_mode()

    def clean_currently_notes_being_played(self):
        if self.app.is_mode_active(self.app.melodic_mode):
            self.app.melodic_mode.remove_all_notes_being_played()
        elif self.app.is_mode_active(self.app.rhyhtmic_mode):
            self.app.rhyhtmic_mode.remove_all_notes_being_played()

    def send_select_track_to_pyramid(self, track_idx):
        # Follows pyramidi specification (Pyramid configured to receive on ch 16)
        msg = mido.Message('control_change', control=0, value=track_idx + 1)
        self.app.send_midi(msg, force_channel=self.pyramidi_channel)

    def select_pyramid_track(self, track_idx):
        self.selected_pyramid_track = track_idx
        self.send_select_track_to_pyramid(self.selected_pyramid_track)
        self.load_current_default_layout()
        self.clean_currently_notes_being_played()
        try:
            self.app.midi_cc_mode.new_track_selected()
        except:
            # Might fail if MIDICCMode not yet initialized?
            pass
        
    def activate(self):
        self.update_buttons()

    def deactivate(self):
        for button_name in self.pyramid_track_button_names_a + self.pyramid_track_button_names_b:
            self.push.buttons.set_button_color(button_name, definitions.BLACK)

    def update_buttons(self):
        for count, name in enumerate(self.pyramid_track_button_names_a):
            color = self.tracks_info[count]['color']
            self.push.buttons.set_button_color(name, color)

        for count, name in enumerate(self.pyramid_track_button_names_b):
            if self.pyramid_track_selection_button_a:
                color = self.tracks_info[self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a)]['color']
                equivalent_track_num = self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a) + count * 8
                if self.selected_pyramid_track == equivalent_track_num:
                    self.push.buttons.set_button_color(name, definitions.WHITE)
                    self.push.buttons.set_button_color(name, color, animation=definitions.DEFAULT_ANIMATION)
                else:
                    self.push.buttons.set_button_color(name, color)
            else:
                color = self.get_current_track_color()
                equivalent_track_num = (self.selected_pyramid_track % 8) + count * 8
                if self.selected_pyramid_track == equivalent_track_num:
                    self.push.buttons.set_button_color(name, definitions.WHITE)
                    self.push.buttons.set_button_color(name, color, animation=definitions.DEFAULT_ANIMATION)
                else:
                    self.push.buttons.set_button_color(name, color)

    def update_display(self, ctx, w, h):

        # Draw track selector labels
        height = 20
        for i in range(0, 8):
            if self.selected_pyramid_track % 8 == i:
                background_color = self.tracks_info[i]['color']
                font_color = definitions.BLACK
            else:
                background_color = definitions.BLACK
                font_color = self.tracks_info[i]['color']
            instrument_short_name = self.tracks_info[i]['instrument_short_name']
            show_text(ctx, i, h - height, instrument_short_name, height=height,
                      font_color=font_color, background_color=background_color)
 
    def on_button_pressed(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            self.pyramid_track_selection_button_a = button_name
            self.pyramid_track_selection_button_a_pressing_time = time.time()
            self.app.buttons_need_update = True
            return True

        elif button_name in self.pyramid_track_button_names_b:
            if self.pyramid_track_selection_button_a:
                # While pressing one of the track selection a buttons
                self.select_pyramid_track(self.pyramid_track_button_names_a.index(
                    self.pyramid_track_selection_button_a) + self.pyramid_track_button_names_b.index(button_name) * 8)
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                return True
            else:
                # No track selection a button being pressed...
                self.select_pyramid_track(self.selected_pyramid_track % 8 + 8 * self.pyramid_track_button_names_b.index(button_name))
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                return True

    def on_button_released(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            if self.pyramid_track_selection_button_a:
                if time.time() - self.pyramid_track_selection_button_a_pressing_time < self.pyramid_track_selection_quick_press_time:
                    # Only switch to track if it was a quick press
                    self.select_pyramid_track(self.pyramid_track_button_names_a.index(button_name))
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                return True
