import push2_python

from definitions import PyshaMode, OFF_BTN_COLOR


class MainControlsMode(PyshaMode):

    def activate(self):
        self.update_buttons()

    def deactivate(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_NOTE, 'black')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_USER, 'black')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_SETUP, 'black')

    def update_buttons(self):
        # Noe button, to toggle melodic/rhythmic mode
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_NOTE, 'white')

        # Mute button, to toggle display on/off
        if self.app.use_push2_display:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_USER, 'white')
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_USER, OFF_BTN_COLOR)

        # Settings button, to toggle settings mode
        if self.app.is_mode_active(self.app.settings_mode):
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_SETUP, 'white', animation='pulsing')
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_SETUP, OFF_BTN_COLOR)

    def on_button_pressed(self, button_name):
        if button_name == push2_python.constants.BUTTON_NOTE:
            self.app.toggle_melodic_rhythmic_modes()
            self.app.pads_need_update = True
            self.app.buttons_need_update = True
        elif button_name == push2_python.constants.BUTTON_SETUP:
            self.app.toggle_and_rotate_settings_mode()
            self.app.buttons_need_update = True
        elif button_name == push2_python.constants.BUTTON_USER:
            self.app.use_push2_display = not self.app.use_push2_display
            if not self.app.use_push2_display:
                self.push.display.send_to_display(self.push.display.prepare_frame(self.push.display.make_black_frame()))
            self.app.buttons_need_update = True
