import push2_python
import mido
import time
import random
import cairo
import numpy


try:
    from settings import MIDI_OUT_DEVICE_NAME, PUSH_MIDI_DEVICE_NAME, USE_PUSH2_DISPLAY
except ImportError:
    MIDI_OUT_DEVICE_NAME = "USB MIDI Device"
    USE_PUSH2_DISPLAY = True
    PUSH_MIDI_DEVICE_NAME = None


# Configure MIDI output port. If Deckard's Dream device is found, send messages to this device.
midi_outport = None
print('Available MIDI device names:')
for name in mido.get_output_names():
    print('\t{0}'.format(name))
try:
    midi_outport = mido.open_output(MIDI_OUT_DEVICE_NAME)
    print('Will send MIDI to port named "{0}"'.format(MIDI_OUT_DEVICE_NAME))
except IOError:
    print('Could not connect to MIDI output port, using virtual MIDI out port')
    midi_outport = mido.open_output('Push2App', virtual=True)


push = push2_python.Push2(push_midi_port_name=PUSH_MIDI_DEVICE_NAME)
push.pads.set_polyphonic_aftertouch()
push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, 'white')
push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, 'white')


# Init variables to store internal state
PADS_STATE = {}
PAD_STATE_ON = True
PAD_STATE_OFF = False
ROOT_MIDI_NOTE = 32  # Pad bottom-left note
SCALE_PATTERN = [True, False, True, False, True, True, False, True, False, True, False, True]
encoders_state = dict()
max_encoder_value = 100
for encoder_name in push.encoders.available_names:
    encoders_state[encoder_name] = {
        'value': int(random.random() * max_encoder_value),
        'color': [random.random(), random.random(), random.random()],
    }
last_selected_encoder = list(encoders_state.keys())[0]

current_color_matrix = None

# Function that generates the contents of the frame do be displayed
def generate_display_frame(encoder_value, encoder_color, encoder_name):

    # Prepare cairo canvas
    WIDTH, HEIGHT = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
    surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # Draw rectangle with width proportional to encoders' value
    ctx.set_source_rgb(*encoder_color)
    ctx.rectangle(0, 0, WIDTH * (encoder_value/max_encoder_value), HEIGHT)
    ctx.fill()

    # Add text with encoder name and value
    ctx.set_source_rgb(1, 1, 1)
    font_size = HEIGHT//3
    ctx.set_font_size(font_size)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.move_to(10, font_size * 2)
    ctx.show_text("{0}: {1}".format(encoder_name, encoder_value))

    # Turn canvas into numpy array compatible with push.display.display_frame method
    buf = surface.get_data()
    frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
    frame = frame.transpose()
    return frame

# Set up action handlers to react to encoder touches and rotation
@push2_python.on_encoder_rotated()
def on_encoder_rotated(push, encoder_name, increment):
    def update_encoder_value(encoder_idx, increment):
        updated_value = int(encoders_state[encoder_idx]['value'] + increment)
        if updated_value < 0:
            encoders_state[encoder_idx]['value'] = 0
        elif updated_value > max_encoder_value:
            encoders_state[encoder_idx]['value'] = max_encoder_value
        else:
            encoders_state[encoder_idx]['value'] = updated_value

    update_encoder_value(encoder_name, increment)
    global last_selected_encoder
    last_selected_encoder = encoder_name

@push2_python.on_encoder_touched()
def on_encoder_touched(push, encoder_name):
    global last_selected_encoder
    last_selected_encoder = encoder_name


def get_pad_state_key(pad_ij):
    return '{0}_{1}'.format(pad_ij[0], pad_ij[1])


def pad_ij_to_midi_note(pad_ij):
        return ROOT_MIDI_NOTE + ((7 - pad_ij[0]) * 5 + pad_ij[1])


for i in range(0, 8):
    for j in range(0, 8):
        state = {'state': PAD_STATE_OFF, 'midi_note': pad_ij_to_midi_note((i, j))}
        PADS_STATE[get_pad_state_key((i, j))] = state

def get_currently_played_midi_notes():
    return [pad['midi_note'] for pad in PADS_STATE.values() if pad['state'] == PAD_STATE_ON]


def draw_pads():
    global current_color_matrix

    color_matrix = []
    for i in range(0, 8):
        row_colors = []
        for j in range(0, 8):
            key = get_pad_state_key((i, j))
            if PADS_STATE[key]['state'] == PAD_STATE_ON:
                row_colors.append('green')
            elif PADS_STATE[key]['midi_note'] in get_currently_played_midi_notes():
                row_colors.append('green')
            elif (PADS_STATE[key]['midi_note'] - ROOT_MIDI_NOTE) % 12 == 0:
                row_colors.append('yellow')
            else:
                relative_midi_note = (PADS_STATE[key]['midi_note'] - ROOT_MIDI_NOTE) % 12
                if SCALE_PATTERN[relative_midi_note]:
                    row_colors.append('white')
                else:
                    row_colors.append('black')
        color_matrix.append(row_colors)
    
    if color_matrix != current_color_matrix:
        push.pads.set_pads_color(color_matrix)
        current_color_matrix = color_matrix


def draw_ui():
    draw_pads()

    if USE_PUSH2_DISPLAY:
        encoder_value = encoders_state[last_selected_encoder]['value']
        encoder_color = encoders_state[last_selected_encoder]['color']
        frame = generate_display_frame(encoder_value, encoder_color, last_selected_encoder)
        push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)


@push2_python.on_pad_pressed()
def on_pad_pressed(push, pad_n, pad_ij, velocity):
    key = get_pad_state_key(pad_ij)
    PADS_STATE[key]['state'] = PAD_STATE_ON
    msg = mido.Message(
        'note_on', note=pad_ij_to_midi_note(pad_ij), velocity=velocity)
    midi_outport.send(msg)


@push2_python.on_pad_released()
def on_pad_released(push, pad_n, pad_ij, velocity):
    key = get_pad_state_key(pad_ij)
    PADS_STATE[key]['state'] = PAD_STATE_OFF
    msg = mido.Message(
        'note_off', note=pad_ij_to_midi_note(pad_ij), velocity=velocity)
    midi_outport.send(msg)


@push2_python.on_pad_aftertouch()
def on_pad_aftertouch(push, pad_n, pad_ij, velocity):
    # Don't change pad state here, just send the MIDI value
    msg = mido.Message(
        'polytouch', note=pad_ij_to_midi_note(pad_ij), value=velocity)
    midi_outport.send(msg)


@push2_python.on_button_pressed(push2_python.constants.BUTTON_OCTAVE_UP)
def on_octave_up(push):
    global ROOT_MIDI_NOTE
    ROOT_MIDI_NOTE += 12


@push2_python.on_button_pressed(push2_python.constants.BUTTON_OCTAVE_DOWN)
def on_octave_down(push):
    global ROOT_MIDI_NOTE
    ROOT_MIDI_NOTE -= 12


print('App runnnig...')
while True:
    draw_ui()
    time.sleep(1.0/30)  # Sart drawing loop, aim at ~30fps
