import push2_python
import mido
import time
import random
import cairo
import numpy

try:
    from settings import MIDI_OUT_DEVICE_NAME
except ImportError:
    MIDI_OUT_DEVICE_NAME = "USB MIDI Device"
   
try:
    from settings import PUSH_MIDI_DEVICE_NAME
except ImportError:
    PUSH_MIDI_DEVICE_NAME = None

try:
    from settings import USE_PUSH2_DISPLAY
except ImportError:
    USE_PUSH2_DISPLAY = True

try:
    from settings import MIDI_IN_MERGE_DEVICE_NAME
except ImportError:
    MIDI_IN_MERGE_DEVICE_NAME = None

try:
    from settings import MIDI_IN_CHANNEL
except ImportError:
    MIDI_IN_CHANNEL = 0

try:
    from settings import TARGET_FRAME_RATE
except ImportError:
    TARGET_FRAME_RATE = 60


PAD_STATE_ON = True
PAD_STATE_OFF = False

class Push2StandaloneControllerApp(object):

    # midi
    midi_out = None
    midi_in = None

    # push
    push = None

    # state
    actual_frame_rate = 0
    current_frame_rate_measurement = 0
    current_frame_rate_measurement_second = 0
    notes_being_played = []
    root_midi_note = 32
    scale_pattern = [True, False, True, False, True, True, False, True, False, True, False, True]
    encoders_state = {}
    max_encoder_value = 100
    current_color_matrix = None


    def __init__(self):
        self.init_midi()
        self.init_push()
        self.init_state()

        self.update_push2_pads()
        self.update_push2_buttons()


    def init_midi(self):
        print('Available MIDI out device names:')
        for name in mido.get_output_names():
            print('\t{0}'.format(name))

        print('Available MIDI in device names:')
        for name in mido.get_input_names():
            print('\t{0}'.format(name))

        print('Configuring MIDI...')
       
        # MIDI out
        try:
            self.midi_out = mido.open_output(MIDI_OUT_DEVICE_NAME)
            print('Will send MIDI to port named "{0}"'.format(MIDI_OUT_DEVICE_NAME))
        except IOError:
            print('Could not connect to MIDI output port, using virtual MIDI out port')
            self.midi_out = mido.open_output('Push2StandaloneControllerApp', virtual=True)

        # MIDI in
        if MIDI_IN_MERGE_DEVICE_NAME is not None:
            self.midi_in = mido.open_input(MIDI_IN_MERGE_DEVICE_NAME)
            self.midi_in.callback = self.midi_in_handler


    def midi_in_handler(self, msg):

        if hasattr(msg, 'channel') and msg.channel == MIDI_IN_CHANNEL:  # This will rule out sysex and other "strange" messages that don't have channel info
            # Forward message to the MIDI out
            self.midi_out.send(msg)
            
            # Update the list of notes being currently played so push2 pads can be updated accordingly
            if msg.type == "note_on":
                if msg.velocity == 0:
                    self.remove_note_being_played(msg.note, self.midi_in.name)
                else:
                    self.add_note_being_played(msg.note, self.midi_in.name)
            elif msg.type == "note_off":
                self.remove_note_being_played(msg.note, self.midi_in.name)
            self.update_push2_pads()


    def init_push(self):
        print('Configuring Push...')
        self.push = push2_python.Push2(push_midi_port_name=PUSH_MIDI_DEVICE_NAME)
        self.push.pads.set_polyphonic_aftertouch()
        

    def init_state(self):
        for encoder_name in self.push.encoders.available_names:
            self.encoders_state[encoder_name] = {
                'value': int(random.random() * self.max_encoder_value),
                'color': [random.random(), random.random(), random.random()],
            }
        self.last_selected_encoder = list(self.encoders_state.keys())[0]


    def add_note_being_played(self, midi_note, source):
        self.notes_being_played.append({'note': midi_note, 'source': source})

    
    def remove_note_being_played(self, midi_note, source):
        self.notes_being_played = [note for note in self.notes_being_played if note['note'] != midi_note or note['source'] != source] 
        

    def pad_ij_to_midi_note(self, pad_ij):
        return self.root_midi_note + ((7 - pad_ij[0]) * 5 + pad_ij[1])
    
    
    def is_midi_note_root_octave(self, midi_note):
        relative_midi_note = (midi_note - self.root_midi_note) % 12
        return relative_midi_note == 0


    def is_black_key_midi_note(self, midi_note):
        relative_midi_note = (midi_note - self.root_midi_note) % 12
        return not self.scale_pattern[relative_midi_note]


    def is_midi_note_being_played(self, midi_note):
        for note in self.notes_being_played:
            if note['note'] == midi_note:
                return True
        return False


    def get_pad_state_key(self, pad_ij):
        return '{0}_{1}'.format(pad_ij[0], pad_ij[1])


    def update_push2_pads(self):
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                cell_color = 'white'
                corresponding_midi_note = self.pad_ij_to_midi_note([i, j])
                if self.is_black_key_midi_note(corresponding_midi_note): 
                    cell_color = 'black'
                if self.is_midi_note_root_octave(corresponding_midi_note):
                    cell_color = 'yellow'
                if self.is_midi_note_being_played(corresponding_midi_note):
                    cell_color = 'green'
                row_colors.append(cell_color)
            color_matrix.append(row_colors)
        
        self.push.pads.set_pads_color(color_matrix)
        

    def update_push2_buttons(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_DOWN, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_OCTAVE_UP, 'white')


    def generate_display_frame(self, encoder_value, encoder_color, encoder_name):

        # Prepare cairo canvas
        w, h = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
        surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, w, h)
        ctx = cairo.Context(surface)

        # Draw rectangle with width proportional to encoders' value
        ctx.set_source_rgb(*encoder_color)
        ctx.rectangle(0, 0, w * (encoder_value/self.max_encoder_value), h)
        ctx.fill()

        # Add text with encoder name and value
        ctx.set_source_rgb(1, 1, 1)
        font_size = h//3
        ctx.set_font_size(font_size)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(10, font_size * 2)
        ctx.show_text("{0}: {1}".format(encoder_name, encoder_value))

        # Add frame rate indicator
        ctx.set_source_rgb(1, 1, 1)
        font_size = h//8
        ctx.set_font_size(font_size)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(10, font_size * 1.5)
        ctx.show_text("{0} fps".format(self.actual_frame_rate))

        buf = surface.get_data()
        return numpy.ndarray(shape=(h, w), dtype=numpy.uint16, buffer=buf).transpose()


    def update_push2_display(self):
        if USE_PUSH2_DISPLAY:
            encoder_value = self.encoders_state[self.last_selected_encoder]['value']
            encoder_color = self.encoders_state[self.last_selected_encoder]['color']
            frame = self.generate_display_frame(encoder_value, encoder_color, self.last_selected_encoder)
            self.push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)


    def run_loop(self):
        print('App runnnig...')
        while True:
            before_draw_time = time.time()
            
            # Draw ui
            self.update_push2_display()
            
            # Frame rate measurement
            now = time.time()
            self.current_frame_rate_measurement += 1
            if time.time() - self.current_frame_rate_measurement_second > 1.0:
                self.actual_frame_rate = self.current_frame_rate_measurement
                self.current_frame_rate_measurement = 0
                self.current_frame_rate_measurement_second = now
                print('{0} fps'.format(self.actual_frame_rate))
            
            after_draw_time = time.time()

            # Calculate sleep time to aproximate the target frame rate
            sleep_time = (1.0 / TARGET_FRAME_RATE) - (after_draw_time - before_draw_time)
            if sleep_time > 0:
                time.sleep(sleep_time)


    def on_encoder_rotated(self, encoder_name, increment):
        
        def update_encoder_value(encoder_idx, increment):
            updated_value = int(self.encoders_state[encoder_idx]['value'] + increment)
            if updated_value < 0:
                self.encoders_state[encoder_idx]['value'] = 0
            elif updated_value > self.max_encoder_value:
                self.encoders_state[encoder_idx]['value'] = self.max_encoder_value
            else:
                self.encoders_state[encoder_idx]['value'] = updated_value

        update_encoder_value(encoder_name, increment)
        self.last_selected_encoder = encoder_name

    def on_encoder_touched(self, encoder_name):
        self.last_selected_encoder = encoder_name

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        self.add_note_being_played(midi_note, 'push')
        msg = mido.Message('note_on', note=midi_note, velocity=velocity)
        self.midi_out.send(msg)
        self.update_push2_pads()

    def on_pad_released(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        self.remove_note_being_played(midi_note, 'push')
        msg = mido.Message('note_off', note=midi_note, velocity=velocity)
        self.midi_out.send(msg)
        self.update_push2_pads()

    def on_pad_aftertouch(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        msg = mido.Message('polytouch', note=midi_note, value=velocity)
        self.midi_out.send(msg)

    def on_octave_up(self):
        self.root_midi_note += 12
        self.update_push2_pads()

    def on_octave_down(self):
        self.root_midi_note -= 12
        self.update_push2_pads()


# Set up action handlers to react to encoder touches and rotation
@push2_python.on_encoder_rotated()
def on_encoder_rotated(push, encoder_name, increment):
    app.on_encoder_rotated(encoder_name, increment)

@push2_python.on_encoder_touched()
def on_encoder_touched(push, encoder_name):
    app.on_encoder_touched(encoder_name)


# Set up action handlers to react to pads being pressed and released
@push2_python.on_pad_pressed()
def on_pad_pressed(push, pad_n, pad_ij, velocity):
    app.on_pad_pressed(pad_n, pad_ij, velocity)


@push2_python.on_pad_released()
def on_pad_released(push, pad_n, pad_ij, velocity):
    app.on_pad_released(pad_n, pad_ij, velocity)


@push2_python.on_pad_aftertouch()
def on_pad_aftertouch(push, pad_n, pad_ij, velocity):
    app.on_pad_aftertouch(pad_n, pad_ij, velocity)


@push2_python.on_button_pressed(push2_python.constants.BUTTON_OCTAVE_UP)
def on_octave_up(push):
    app.on_octave_up()


@push2_python.on_button_pressed(push2_python.constants.BUTTON_OCTAVE_DOWN)
def on_octave_down(push):
    app.on_octave_down()


if __name__ == "__main__":
    app = Push2StandaloneControllerApp()
    app.run_loop()