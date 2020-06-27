VERSION = '0.2'

PYRAMIDI_CHANNEL = 15

DELAYED_ACTIONS_APPLY_TIME = 1.0  # Encoder changes won't be applied until this time has passed since last moved

LAYOUT_MELODIC = 'lmelodic'
LAYOUT_RHYTHMIC = 'lrhytmic'

BLACK_RGB = [0, 0, 0]
GRAY_DARK_RGB = [30, 30, 30]
GRAY_LIGHT_RGB = [180, 180, 180]
WHITE_RGB = [255, 255, 255]
YELLOW_RGB = [255, 241, 0]
ORANGE_RGB = [255, 140, 0]
RED_RGB = [232, 17, 35]
PINK_RGB = [236, 0, 140]
PURPLE_RGB = [104, 33, 122]
BLUE_RGB = [0, 24, 143]
CYAN_RGB = [0, 188, 242]
TURQUOISE_RGB = [0, 178, 148]
GREEN_RGB = [0, 158, 73]
LIME_RGB = [186, 216, 10]

BLACK = 'black'
GRAY_DARK = 'gray_dark'
GRAY_LIGHT = 'gray_light'
WHITE = 'white'
YELLOW = 'yellow'
ORANGE = 'orange'
RED = 'red'
PINK = 'pink'
PURPLE = 'purple'
BLUE = 'blue'
CYAN = 'cyan'
TURQUOISE = 'turquoise'
GREEN = 'green'
LIME = 'lime'

COLORS_NAMES = [BLACK, GRAY_DARK, GRAY_LIGHT, WHITE, YELLOW, ORANGE, RED, PINK, PURPLE, BLUE, CYAN, TURQUOISE, GREEN, LIME]

def get_color_rgb(color_name):
    return globals().get('{0}_RGB'.format(color_name.upper()), [0, 0, 0])

def get_color_rgb_float(color_name):
    return [x/255 for x in get_color_rgb(color_name)]

FONT_COLOR_DELAYED_ACTIONS = ORANGE
FONT_COLOR_DISABLED = GRAY_LIGHT
OFF_BTN_COLOR = GRAY_DARK
NOTE_ON_COLOR = GREEN



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
