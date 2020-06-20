import mido
import push2_python
import time

from definitions import PyshaMode, OFF_BTN_COLOR


class PyramidiMode(PyshaMode):

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
    pyramid_track_selection_quick_press_time = 0.200
    pyramidi_channel = 15

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
            if self.selected_pyramid_track % 8 == count:
                self.push.buttons.set_button_color(name, 'green')
            else:
                self.push.buttons.set_button_color(name, 'orange')

        for count, name in enumerate(self.pyramid_track_button_names_b):
            if self.pyramid_track_selection_button_a:
                if self.selected_pyramid_track // 8 == count:
                    self.push.buttons.set_button_color(name, 'green', animation='pulsing')
                else:
                    self.push.buttons.set_button_color(name, 'orange', animation='pulsing')
            else:
                self.push.buttons.set_button_color(name, 'black')
    
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
                self.send_select_track_to_pyramid(self.selected_pyramid_track)
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0

    def on_button_released(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            if self.pyramid_track_selection_button_a:
                if time.time() - self.pyramid_track_selection_button_a_pressing_time < self.pyramid_track_selection_quick_press_time:
                    # Only switch to track if it was a quick press
                    self.selected_pyramid_track = self.pyramid_track_button_names_a.index(button_name)
                    self.send_select_track_to_pyramid(self.selected_pyramid_track)
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                self.app.buttons_need_update = True
