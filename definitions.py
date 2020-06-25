VERSION = '0.1'

DELAYED_ACTIONS_APPLY_TIME = 1.0  # Encoder changes won't be applied until this time has passed since last moved
FONT_COLOR_DELAYED_ACTIONS = [1.0, 0.64, 0.0]
FONT_COLOR_DISABLED = [0.5, 0.5, 0.5]
OFF_BTN_COLOR = 'my_dark_gray'

LAYOUT_MELODIC = 'lmelodic'
LAYOUT_RHYTHMIC = 'lrhytmic'

class PyshaMode(object):
    """
    """

    name = ''

    def __init__(self, app, settings=None):
        self.app = app
        self.initialize(settings=settings)

    @property
    def push(self):
        return self.app.push

    # Method run only once when the mode object is created, may receive settings dictionary from main app
    def initialize(self, settings=None):
        pass

    # Method to return a dictionary of properties to store in a settings file, and that will be passed to
    # initialize method when object created
    def get_settings_to_save(self):
        return {}

    # Methods that are run before the mode is activated and when it is deactivated
    def activate(self):
        pass

    def deactivate(self):
        pass

    # Method called at every iteration in the main loop to see if any actions need to be performed at the end of the iteration
    # This is used to avoid some actions unncessesarily being repeated many times
    def check_for_delayed_actions(self):
        pass

    # Method called when MIDI messages arrive from Pysha MIDI input
    def on_midi_in(self, msg):
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
