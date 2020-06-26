import push2_python

from definitions import PyshaMode, OFF_BTN_COLOR

TOGGLE_DISPLAY_BUTTON = push2_python.constants.BUTTON_USER
SETTINGS_BUTTON = push2_python.constants.BUTTON_SETUP
MELODIC_RHYTHMIC_TOGGLE_BUTTON = push2_python.constants.BUTTON_NOTE


class MainControlsMode(PyshaMode):

    def activate(self):
        self.update_buttons()

    def deactivate(self):
        self.push.buttons.set_button_color(MELODIC_RHYTHMIC_TOGGLE_BUTTON, 'black')
        self.push.buttons.set_button_color(TOGGLE_DISPLAY_BUTTON, 'black')
        self.push.buttons.set_button_color(SETTINGS_BUTTON, 'black')

    def update_buttons(self):
        # Noe button, to toggle melodic/rhythmic mode
        self.push.buttons.set_button_color(MELODIC_RHYTHMIC_TOGGLE_BUTTON, 'white')

        # Mute button, to toggle display on/off
        if self.app.use_push2_display:
            self.push.buttons.set_button_color(TOGGLE_DISPLAY_BUTTON, 'white')
        else:
            self.push.buttons.set_button_color(TOGGLE_DISPLAY_BUTTON, OFF_BTN_COLOR)

        # Settings button, to toggle settings mode
        if self.app.is_mode_active(self.app.settings_mode):
            self.push.buttons.set_button_color(SETTINGS_BUTTON, 'white', animation='pulsing')
        else:
            self.push.buttons.set_button_color(SETTINGS_BUTTON, OFF_BTN_COLOR)

    def on_button_pressed(self, button_name):
        if button_name == MELODIC_RHYTHMIC_TOGGLE_BUTTON:
            self.app.toggle_melodic_rhythmic_modes()
            self.app.pads_need_update = True
            self.app.buttons_need_update = True
        elif button_name == SETTINGS_BUTTON:
            self.app.toggle_and_rotate_settings_mode()
            self.app.buttons_need_update = True
        elif button_name == TOGGLE_DISPLAY_BUTTON:
            self.app.use_push2_display = not self.app.use_push2_display
            if not self.app.use_push2_display:
                self.push.display.send_to_display(self.push.display.prepare_frame(self.push.display.make_black_frame()))
            self.app.buttons_need_update = True
