DELAYED_ACTIONS_APPLY_TIME = 1.0  # Encoder changes won't be applied until this time has passed since last moved
OFF_BTN_COLOR = 'my_dark_gray'

class PyshaMode(object):
    """
    """

    name = ''

    def __init__(self, app):
        self.app = app
        self.initialize()

    @property
    def push(self):
        return self.app.push

    # Method run only once when the mode object is created
    def initialize(self):
        pass

    # Methhods that are run before the mode is activated and when it is deactivated
    def activate(self):
        pass

    def deactivate(self):
        pass

    # Push2 update methods
    def update_pads(self):
        pass

    def update_buttons(self):
        pass

    def update_display(self, ctx, w, h):
        pass

    # Push2 action callbacks
    def on_encoder_rotated(self, encoder_name, increment):
        pass

    def on_button_pressed(self, button_name):
        pass

    def on_button_released(self, button_name):
        pass

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        pass

    def on_pad_released(self, pad_n, pad_ij, velocity):
        pass

    def on_pad_aftertouch(self, pad_n, pad_ij, velocity):
        pass

    def on_touchstrip(self, value):
        pass

    def on_sustain_pedal(self, sustain_on):
        pass
