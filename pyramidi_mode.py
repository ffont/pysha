import mido
import push2_python
import time

from definitions import PyshaMode, OFF_BTN_COLOR, LAYOUT_MELODIC, LAYOUT_RHYTHMIC
from display_utils import draw_text_at


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
    pyramidi_channel = 15

    def initialize(self, settings=None):
        # TODO: tracks info could be loaed from some json file, including extra stuff like main MIDI CCs, etc
        for i in range(0, 64):
            data = {
                'track_name': '{0}{1}'.format((i % 16) + 1, ['A', 'B', 'C', 'D'][i//16]),
                'instrument_name': '-',
                'instrument_short_name': '-',
                'color': 'my_dark_gray',
                'color_rgb': [26/255, 26/255, 26/255],
                'default_layout': LAYOUT_MELODIC,
            }
            if i % 8 == 0:
                data['instrument_name'] = 'Deckard\'s Dream'
                data['instrument_short_name'] = 'DDRM'
                data['color'] = 'orange'
                data['color_rgb'] = [255/255, 153/255, 0/255]
            elif i % 8 == 1:
                data['instrument_name'] = 'Minitaur'
                data['instrument_short_name'] = 'MINITAUR'
                data['color'] = 'yellow'
                data['color_rgb'] = [253/255, 208/255, 35/255]
            elif i % 8 == 2:
                data['instrument_name'] = 'Dominion'
                data['instrument_short_name'] = 'DOMINON'
                data['color'] = 'turquoise'
                data['color_rgb'] = [0/255, 116/255, 252/255]
            elif i % 8 == 3:
                data['instrument_name'] = 'Kijimi'
                data['instrument_short_name'] = 'KIJIMI'
                data['color'] = 'green'
                data['color_rgb'] = [0/255, 255/255, 0/255]
            elif i % 8 == 4:
                data['instrument_name'] = 'Black Box (Pads)'
                data['instrument_short_name'] = 'BBPADS'
                data['color'] = 'red'
                data['color_rgb'] = [255/255, 0/255, 0/255]
                data['default_layout'] = LAYOUT_RHYTHMIC
            elif i % 8 == 5:
                data['instrument_name'] = 'Black Box (Notes)'
                data['instrument_short_name'] = 'BBNOTES'
                data['color'] = 'pink'
                data['color_rgb'] = [255/255, 8/255, 74/255]
            self.tracks_info.append(data)

    def get_current_track_color(self):
        return self.tracks_info[self.selected_pyramid_track]['color']

    def get_current_track_color_rgb(self):
        return self.tracks_info[self.selected_pyramid_track]['color_rgb']

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

    def activate(self):
        self.update_buttons()

    def deactivate(self):
        for button_name in self.pyramid_track_button_names_a + self.pyramid_track_button_names_b:
            self.push.buttons.set_button_color(button_name, 'black')

    def update_buttons(self):
        for count, name in enumerate(self.pyramid_track_button_names_a):
            color = self.tracks_info[count]['color']
            self.push.buttons.set_button_color(name, color)

        for count, name in enumerate(self.pyramid_track_button_names_b):
            if self.pyramid_track_selection_button_a:
                equivalent_track_num = self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a) + count * 8
                if self.selected_pyramid_track == equivalent_track_num:
                    self.push.buttons.set_button_color(name, 'green', animation='pulsing')
                else:
                    color = self.tracks_info[self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a)]['color']
                    self.push.buttons.set_button_color(name, color)
            else:
                self.push.buttons.set_button_color(name, 'black')

    def update_display(self, ctx, w, h):

        # Divide display in 8 parts to show different settings
        part_w = w // 8
        part_h = h

        # Draw track selector labels
        for i in range(0, 8):
            part_x = i * part_w
            if self.selected_pyramid_track % 8 == i:
                rectangle_color = self.tracks_info[i]['color_rgb']
                font_color = [1, 1, 1]
            else:
                rectangle_color = [0, 0, 0]
                font_color = self.tracks_info[i]['color_rgb']
            rectangle_height = 20
            ctx.set_source_rgb(*rectangle_color)
            ctx.rectangle(part_x, part_h - rectangle_height, w, part_h)
            ctx.fill()
            instrument_short_name = self.tracks_info[i]['instrument_short_name']
            draw_text_at(ctx, part_x + 3, part_h - 4, instrument_short_name, font_size=15, color=font_color) 

        # Draw main track info
        font_color = [1, 1, 1] #self.get_current_track_color_rgb()
        rectangle_color = [0, 0, 0]
        rectangle_height_width = (h - 20 - 20)/1.5
        ctx.set_source_rgb(*rectangle_color)
        x = 0
        y = (h - rectangle_height_width)/2 - 10
        font_size = 30
        #ctx.rectangle(x, y, rectangle_height_width, rectangle_height_width)
        #ctx.fill()
        draw_text_at(ctx, x + 3, y + 50, '{1} {0}'.format(self.tracks_info[self.selected_pyramid_track]['instrument_name'],
                                                               self.tracks_info[self.selected_pyramid_track]['track_name']), font_size=font_size, color=font_color)

    
    def on_button_pressed(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            self.pyramid_track_selection_button_a = button_name
            self.pyramid_track_selection_button_a_pressing_time = time.time()
            self.app.buttons_need_update = True

        elif button_name in self.pyramid_track_button_names_b:
            if self.pyramid_track_selection_button_a:
                self.selected_pyramid_track = self.pyramid_track_button_names_a.index(
                    self.pyramid_track_selection_button_a) + self.pyramid_track_button_names_b.index(button_name) * 8
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                self.send_select_track_to_pyramid(self.selected_pyramid_track)
                self.load_current_default_layout()
                self.clean_currently_notes_being_played()
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0

    def on_button_released(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            if self.pyramid_track_selection_button_a:
                if time.time() - self.pyramid_track_selection_button_a_pressing_time < self.pyramid_track_selection_quick_press_time:
                    # Only switch to track if it was a quick press
                    self.selected_pyramid_track = self.pyramid_track_button_names_a.index(button_name)
                    self.send_select_track_to_pyramid(self.selected_pyramid_track)
                    self.load_current_default_layout()
                    self.clean_currently_notes_being_played()
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
