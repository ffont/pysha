import push2_python
import mido
import time
import random
import cairo
import numpy

try:
    from settings import MIDI_OUT_DEFAULT_DEVICE_NAME
except ImportError:
    MIDI_OUT_DEFAULT_DEVICE_NAME = None
   
try:
    from settings import PUSH_MIDI_DEVICE_NAME
except ImportError:
    PUSH_MIDI_DEVICE_NAME = None

try:
    from settings import USE_PUSH2_DISPLAY
except ImportError:
    USE_PUSH2_DISPLAY = True

try:
    from settings import MIDI_IN_MERGE_DEFAULT_DEVICE_NAME
except ImportError:
    MIDI_IN_MERGE_DEFAULT_DEVICE_NAME = None

try:
    from settings import MIDI_IN_DEFAULT_CHANNEL
except ImportError:
    MIDI_IN_DEFAULT_CHANNEL = 0

try:
    from settings import MIDI_OUT_DEFAULT_CHANNEL
except ImportError:
    MIDI_OUT_DEFAULT_CHANNEL = 0

try:
    from settings import TARGET_FRAME_RATE
except ImportError:
    TARGET_FRAME_RATE = 60


PAD_STATE_ON = True
PAD_STATE_OFF = False
DELAYED_ACTIONS_APPLY_TIME = 1.0  # Encoder changes won't be applied until this time has passed since last moved

class Push2StandaloneControllerApp(object):

    # midi
    midi_out = None
    available_midi_out_device_names = []
    midi_out_channel = 0  # 0-15
    midi_out_tmp_device_idx = None  # This is to store device names while rotating encoders
    
    midi_in = None
    available_midi_in_device_names = []
    midi_in_channel = 0  # 0-15
    midi_in_tmp_device_idx = None  # This is to store device names while rotating encoders
    

    # push
    push = None

    # state
    actual_frame_rate = 0
    current_frame_rate_measurement = 0
    current_frame_rate_measurement_second = 0
    notes_being_played = []
    root_midi_note = 64
    scale_pattern = [True, False, True, False, True, True, False, True, False, True, False, True]
    encoders_state = {}
    pads_need_update = True
    buttons_need_update = True

    def __init__(self):
        self.set_midi_in_channel(MIDI_IN_DEFAULT_CHANNEL)
        self.set_midi_out_channel(MIDI_OUT_DEFAULT_CHANNEL)
        self.init_midi_in()
        self.init_midi_out()
        self.init_push()
        self.init_state()


    def init_midi_in(self, device_name=MIDI_IN_MERGE_DEFAULT_DEVICE_NAME):
        print('Configuring MIDI in...')
        self.available_midi_in_device_names = mido.get_input_names()
        
        if device_name is not None:
            if self.midi_in is not None:
                    self.midi_in.callback = None  # Disable current callback (if any)
            try:
                self.midi_in = mido.open_input(device_name)
                self.midi_in.callback = self.midi_in_handler
                print('Receiving MIDI in from "{0}"'.format(device_name))
            except IOError:
                print('Could not connect to MIDI input port "{0}"\nAvailable device names:'.format(device_name))
                for name in self.available_midi_in_device_names:
                    print(' - {0}'.format(name))
        else:
            if self.midi_in is not None:
                self.midi_in.callback = None # Disable current callback (if any)
                self.midi_in = None
            
        if self.midi_in is None:
            print('Not receiving from any MIDI input')


    def init_midi_out(self, device_name=MIDI_OUT_DEFAULT_DEVICE_NAME):
        print('Configuring MIDI out...')
        self.available_midi_out_device_names = mido.get_output_names()
       
        if device_name is not None:
            try:
                self.midi_out = mido.open_output(device_name)
                print('Will send MIDI to "{0}"'.format(device_name))
            except IOError as e:
                print('Could not connect to MIDI output port "{0}"\nAvailable device names:'.format(device_name))
                for name in self.available_midi_out_device_names:
                    print(' - {0}'.format(name))
        else:
            if self.midi_out is not None:
                self.midi_out = None

        if self.midi_out is None:
            print('Won\'t send MIDI to any device')

    
    def set_midi_in_channel(self, channel):
        self.midi_in_channel = channel
        if self.midi_in_channel < 0:
            self.midi_in_channel = 0
        elif self.midi_in_channel > 15:
            self.midi_in_channel = 15


    def set_midi_out_channel(self, channel):
        self.midi_out_channel = channel
        if self.midi_out_channel < 0:
            self.midi_out_channel = 0
        elif self.midi_out_channel > 15:
            self.midi_out_channel = 15


    def set_midi_in_device_by_index(self, device_idx):
        if device_idx >= 0 and device_idx < len(self.available_midi_in_device_names):
            self.init_midi_in(self.available_midi_in_device_names[device_idx])
        else:
            self.init_midi_in(None)


    def set_midi_out_device_by_index(self, device_idx):
        if device_idx >= 0 and device_idx < len(self.available_midi_out_device_names):
            self.init_midi_out(self.available_midi_out_device_names[device_idx])
        else:
            self.init_midi_out(None)


    def send_midi(self, msg):
        if self.midi_out is not None:
            self.midi_out.send(msg)


    def midi_in_handler(self, msg):

        if hasattr(msg, 'channel') and msg.channel == self.midi_in_channel:  # This will rule out sysex and other "strange" messages that don't have channel info
            # Forward message to the MIDI out
            self.send_midi(msg)
            
            # Update the list of notes being currently played so push2 pads can be updated accordingly
            if msg.type == "note_on":
                if msg.velocity == 0:
                    self.remove_note_being_played(msg.note, self.midi_in.name)
                else:
                    self.add_note_being_played(msg.note, self.midi_in.name)
            elif msg.type == "note_off":
                self.remove_note_being_played(msg.note, self.midi_in.name)
            self.pads_need_update = True  # Using the async update method because we don't really need immediate response here


    def init_push(self):
        print('Configuring Push...')
        self.push = push2_python.Push2(push_midi_port_name=PUSH_MIDI_DEVICE_NAME)
        self.push.pads.set_polyphonic_aftertouch()
        

    def init_state(self):
        current_time = time.time()
        self.last_time_pads_updated = current_time
        self.last_time_buttons_updated = current_time
        for encoder_name in self.push.encoders.available_names:
            self.encoders_state[encoder_name] = {
                'last_message_received': current_time,
            }


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

    
    def note_number_to_name(self, note_number):
        semis = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note_number = int(round(note_number))
        return semis[note_number % 12] + str(note_number//12 - 1)


    def set_root_midi_note(self, note_number):
        self.root_midi_note = note_number
        if self.root_midi_note < 0:
            self.root_midi_note = 0
        elif self.root_midi_note > 127:
            self.root_midi_note = 127


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


    def generate_display_frame(self):

        def show_title(x, text, color=[1, 1, 1]):
            text = str(text)
            ctx.set_source_rgb(*color)
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            font_size = h//12
            ctx.set_font_size(font_size)
            ctx.move_to(x + 3, 20)
            ctx.show_text(text)

        def show_value(x, text, color=[1, 1, 1]):
            text = str(text)
            ctx.set_source_rgb(*color)
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            font_size = h//8
            ctx.set_font_size(font_size)
            ctx.move_to(x + 3, 45)
            ctx.show_text(text)

        # Prepare cairo canvas
        w, h = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
        surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, w, h)
        ctx = cairo.Context(surface)

        # Divide display in 8 parts to show different settings
        part_w = w // 8
        part_h = h
        for i in range(0, 8):
            part_x = i * part_w 
            part_y = 0

            ctx.set_source_rgb(0, 0, 0)  # Draw black background
            ctx.rectangle(part_x - 3, part_y, w, h)  # do x -3 to add some margin between parts
            ctx.fill()

            color = [1.0, 1.0, 1.0]
            
            if i==0:  # MIDI in device
                if self.midi_in_tmp_device_idx is not None:
                    color = [0.0, 1.0, 0.0]  # Green font
                    if self.midi_in_tmp_device_idx < 0:
                        name = "None"
                    else:
                        name = self.available_midi_in_device_names[self.midi_in_tmp_device_idx]
                else:
                    if self.midi_in is not None:
                        name = self.midi_in.name
                    else:
                        color = [0.5, 0.5, 0.5]  # Gray font
                        name = "None"
                show_title(part_x, 'IN DEVICE')
                show_value(part_x, name, color)
                
            elif i==1:  # MIDI in channel
                if self.midi_in is None:
                    color = [0.5, 0.5, 0.5]  # Gray font
                show_title(part_x, 'IN CH')
                show_value(part_x, self.midi_in_channel, color)

            elif i==2:  # MIDI out device
                if self.midi_out_tmp_device_idx is not None:
                    color = [0.0, 1.0, 0.0]  # Green font
                    if self.midi_out_tmp_device_idx < 0:
                        name = "None"
                    else:
                        name = self.available_midi_out_device_names[self.midi_out_tmp_device_idx]
                else:
                    if self.midi_out is not None:
                        name = self.midi_out.name
                    else:
                        color = [0.5, 0.5, 0.5]  # Gray font
                        name = "None"
                show_title(part_x, 'OUT DEVICE')
                show_value(part_x, name, color)

            elif i==3:  # MIDI out channel
                if self.midi_out is None:
                    color = [0.5, 0.5, 0.5]  # Gray font
                show_title(part_x, 'OUT CH')
                show_value(part_x, self.midi_out_channel, color)

            elif i==4:  # Root note
                show_title(part_x, 'ROOT NOTE')
                show_value(part_x, self.note_number_to_name(self.root_midi_note), color)

            elif i==5:  # Empty
                pass
            elif i==6:  # Empty
                pass
            elif i==7:  # FPS indicator
                show_title(part_x, 'FPS')
                show_value(part_x, self.actual_frame_rate, color)

        buf = surface.get_data()
        return numpy.ndarray(shape=(h, w), dtype=numpy.uint16, buffer=buf).transpose()


    def check_for_delayed_actions(self):
        current_time = time.time()

        if self.midi_in_tmp_device_idx is not None:
            # Means we are in the process of changing the MIDI in device
            if current_time - self.encoders_state['Track1 Encoder']['last_message_received'] > DELAYED_ACTIONS_APPLY_TIME:
                self.set_midi_in_device_by_index(self.midi_in_tmp_device_idx)
                self.midi_in_tmp_device_idx = None

        if self.midi_out_tmp_device_idx is not None:
            # Means we are in the process of changing the MIDI in device
            if current_time - self.encoders_state['Track3 Encoder']['last_message_received'] > DELAYED_ACTIONS_APPLY_TIME:
                self.set_midi_out_device_by_index(self.midi_out_tmp_device_idx)
                self.midi_out_tmp_device_idx = None

        if self.pads_need_update:
            self.update_push2_pads()
            self.pads_need_update = False

        if self.buttons_need_update:
            self.update_push2_buttons()
            self.pads_need_update = False


    def update_push2_display(self):
        if USE_PUSH2_DISPLAY:
            frame = self.generate_display_frame()
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
            
            # Check if any delayed actions need to be applied
            self.check_for_delayed_actions()

            after_draw_time = time.time()

            # Calculate sleep time to aproximate the target frame rate
            sleep_time = (1.0 / TARGET_FRAME_RATE) - (after_draw_time - before_draw_time)
            if sleep_time > 0:
                time.sleep(sleep_time)


    def on_encoder_rotated(self, encoder_name, increment):

        self.encoders_state[encoder_name]['last_message_received'] = time.time()

        if encoder_name == 'Track1 Encoder':
            if self.midi_in_tmp_device_idx is None:
                if self.midi_in is not None:
                    self.midi_in_tmp_device_idx = self.available_midi_in_device_names.index(self.midi_in.name)
                else:
                    self.midi_in_tmp_device_idx = -1
            self.midi_in_tmp_device_idx += increment
            if self.midi_in_tmp_device_idx >= len(self.available_midi_in_device_names):
                self.midi_in_tmp_device_idx = len(self.available_midi_in_device_names) - 1
            elif self.midi_in_tmp_device_idx < -1:
                self.midi_in_tmp_device_idx = -1  # Will use -1 for "None"
        
        elif encoder_name == 'Track2 Encoder':
            self.set_midi_in_channel(self.midi_in_channel + increment)
        
        elif encoder_name == 'Track3 Encoder':
            if self.midi_out_tmp_device_idx is None:
                if self.midi_out is not None:
                    self.midi_out_tmp_device_idx = self.available_midi_out_device_names.index(self.midi_out.name)
                else:
                    self.midi_out_tmp_device_idx = -1
            self.midi_out_tmp_device_idx += increment
            if self.midi_out_tmp_device_idx >= len(self.available_midi_out_device_names):
                self.midi_out_tmp_device_idx = len(self.available_midi_out_device_names) - 1
            elif self.midi_out_tmp_device_idx < -1:
                self.midi_out_tmp_device_idx = -1  # Will use -1 for "None"
        
        elif encoder_name == 'Track4 Encoder':
            self.set_midi_out_channel(self.midi_out_channel + increment)
        
        elif encoder_name == 'Track5 Encoder':
            self.set_root_midi_note(self.root_midi_note + increment)
            self.pads_need_update = True  # Using async update method because we don't really need immediate response here

    def on_pad_pressed(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        self.add_note_being_played(midi_note, 'push')
        msg = mido.Message('note_on', note=midi_note, velocity=velocity)
        self.send_midi(msg)
        self.update_push2_pads()  # Directly calling update pads method because we want user to feel feedback as quick as possible

    def on_pad_released(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        self.remove_note_being_played(midi_note, 'push')
        msg = mido.Message('note_off', note=midi_note, velocity=velocity)
        self.send_midi(msg)
        self.update_push2_pads()  # Directly calling update pads method because we want user to feel feedback as quick as possible

    def on_pad_aftertouch(self, pad_n, pad_ij, velocity):
        midi_note = self.pad_ij_to_midi_note(pad_ij)
        msg = mido.Message('polytouch', note=midi_note, value=velocity)
        self.send_midi(msg)

    def on_octave_up(self):
        self.set_root_midi_note(self.root_midi_note + 12)
        self.pads_need_update = True  # Using async update method because we don't really need immediate response here
        self.buttons_need_update = True

    def on_octave_down(self):
        self.set_root_midi_note(self.root_midi_note - 12)
        self.pads_need_update = True  # Using async update method because we don't really need immediate response here
        self.buttons_need_update = True

    def on_touchstrip(self, value):
        msg = mido.Message('pitchwheel', pitch=value)
        self.send_midi(msg)


# Set up action handlers to react to encoder touches and rotation
@push2_python.on_encoder_rotated()
def on_encoder_rotated(push, encoder_name, increment):
    app.on_encoder_rotated(encoder_name, increment)


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


@push2_python.on_touchstrip()
def on_touchstrip(push, value):
    app.on_touchstrip(value)


if __name__ == "__main__":
    app = Push2StandaloneControllerApp()
    app.run_loop()
