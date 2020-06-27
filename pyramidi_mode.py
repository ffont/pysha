import definitions
import mido
import push2_python
import time
import math

from definitions import PyshaMode, OFF_BTN_COLOR, LAYOUT_MELODIC, LAYOUT_RHYTHMIC, PYRAMIDI_CHANNEL
from display_utils import draw_text_at, show_title, show_value


# TODO: this shoud be loaded from some definition file(s)
synth_midi_control_cc_data = {
    'DDRM': [
        {
            'section': 'GLOBAL',
            'controls': [('BRILL', 109),
                            ('RESSO', 110),
                            ('FEET1', 102),
                            ('FEET2', 103)],
        },{
            'section': 'VCO I',
            'controls': [('SPEED', 40),
                            ('PWM', 41),
                            ('PW', 42)],
        },{
            'section': 'VCO II',
            'controls': [('SPEED', 67),
                            ('PWM', 68),
                            ('PW', 69)],
        }
    ],
    'MINITAUR': [
        {
            'section': 'VCO',
            'controls': [('VCO1 LEV', 15),
                            ('VCO2 LEV', 16)],
        },{
            'section': 'VCF',
            'controls': [('CUTOFF', 19),
                            ('RESSO', 21)],
        },{
            'section': 'LFO',
            'controls': [('VCO AMT', 13),
                            ('VCF AMT', 12)],
        }
    ]
}

class MIDICCControl(object):

    color = definitions.GRAY_LIGHT
    color_rgb = None
    name = 'Unknown'
    section = 'unknown'
    cc_number = 10
    value = 64
    vmin = 0
    vmax = 127
    get_color_func = None
    send_midi_func = None

    def __init__(self, cc_number, name, section_name, get_color_func, send_midi_func):
        self.cc_number = cc_number
        self.name = name
        self.section = section_name
        self.get_color_func = get_color_func
        self.send_midi_func = send_midi_func

    def draw(self, ctx, x, y):
        color = self.get_color_func()
        show_title(ctx, x, y, '{0} - {1}'.format(self.name, self.section), color=definitions.get_color_rgb_float(definitions.WHITE))
        show_value(ctx, x, y+30, self.value, color=color)

        radius = 25
        start_rad = 130 * (math.pi / 180)
        end_rad = 50 * (math.pi / 180)
        xc = x + radius + 3
        yc = y - 70

        def get_rad_for_value(value):
            total_degrees = 280
            # TODO: include vmin here to make it more generic
            return start_rad + total_degrees * (value/self.vmax)  * (math.pi / 180)

        # This is needed to prevent showing line from previous position
        ctx.set_source_rgb(0, 0, 0)
        ctx.stroke() 

        # Inner circle
        ctx.arc(xc, yc, radius, start_rad, end_rad)
        ctx.set_source_rgb(*definitions.get_color_rgb_float(definitions.GRAY_LIGHT))
        ctx.set_line_width(1)
        ctx.stroke()

        # Outer circle
        ctx.arc(xc, yc, radius, start_rad, get_rad_for_value(self.value))
        ctx.set_source_rgb(*color)
        ctx.set_line_width(3)
        ctx.stroke()

    
    def update_value(self, increment): 
        if self.value + increment > self.vmax:
            self.value = self.vmax
        elif self.value + increment < self.vmin:
            self.value = self.vmin
        else:
            self.value += increment

        msg = mido.Message('control_change', control=self.cc_number, value=self.value)
        self.send_midi_func(msg)


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
    pyramidi_channel = PYRAMIDI_CHANNEL

    synth_midi_control_ccs = {}
    active_midi_control_ccs = []

    def initialize(self, settings=None):
        # TODO: tracks info could be loaed from some json file, including extra stuff like main MIDI CCs, etc
        for i in range(0, 64):
            data = {
                'track_name': '{0}{1}'.format((i % 16) + 1, ['A', 'B', 'C', 'D'][i//16]),
                'instrument_name': '-',
                'instrument_short_name': '-',
                'color': definitions.GRAY_DARK,
                'default_layout': LAYOUT_MELODIC,
            }
            if i % 8 == 0:
                data['instrument_name'] = 'Deckard\'s Dream'
                data['instrument_short_name'] = 'DDRM'
                data['color'] = definitions.ORANGE
            elif i % 8 == 1:
                data['instrument_name'] = 'Minitaur'
                data['instrument_short_name'] = 'MINITAUR'
                data['color'] = definitions.YELLOW
            elif i % 8 == 2:
                data['instrument_name'] = 'Dominion'
                data['instrument_short_name'] = 'DOMINON'
                data['color'] = definitions.TURQUOISE
            elif i % 8 == 3:
                data['instrument_name'] = 'Kijimi'
                data['instrument_short_name'] = 'KIJIMI'
                data['color'] = definitions.LIME
            elif i % 8 == 4:
                data['instrument_name'] = 'Black Box (Pads)'
                data['instrument_short_name'] = 'BBPADS'
                data['color'] = definitions.RED
                data['default_layout'] = LAYOUT_RHYTHMIC
            elif i % 8 == 5:
                data['instrument_name'] = 'Black Box (Notes)'
                data['instrument_short_name'] = 'BBNOTES'
                data['color'] = definitions.PINK
            self.tracks_info.append(data)

        for synth_name, data in synth_midi_control_cc_data.items():
            self.synth_midi_control_ccs[synth_name] = []
            for section in data:
                section_name = section['section']
                for name, cc_number in section['controls']:
                    control = MIDICCControl(cc_number, name, section_name, self.get_current_track_color_rgb, self.app.send_midi)
                    self.synth_midi_control_ccs[synth_name].append(control)
        
        self.select_pyramid_track(self.selected_pyramid_track)


    def get_current_track_instrument_short_name(self):
        return self.tracks_info[self.selected_pyramid_track]['instrument_short_name']

    def get_current_track_color(self):
        return self.tracks_info[self.selected_pyramid_track]['color']

    def get_current_track_color_rgb(self):
        return definitions.get_color_rgb_float(self.get_current_track_color())

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

    def select_pyramid_track(self, track_idx):
        self.selected_pyramid_track = track_idx
        self.send_select_track_to_pyramid(self.selected_pyramid_track)
        self.load_current_default_layout()
        self.clean_currently_notes_being_played()
        self.active_midi_control_ccs = self.synth_midi_control_ccs.get(self.get_current_track_instrument_short_name(), [])

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

        if self.active_midi_control_ccs:
            # Draw midi contorl ccs
            for i in range(0, min(len(self.active_midi_control_ccs), 8)):
                part_x = i * part_w
                self.active_midi_control_ccs[i].draw(ctx, part_x, part_h)
        else:
            # Draw track info
            font_color = [1, 1, 1]
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

        # Draw track selector labels
        for i in range(0, 8):
            part_x = i * part_w
            if self.selected_pyramid_track % 8 == i:
                rectangle_color = definitions.get_color_rgb_float(self.tracks_info[i]['color'])
                font_color = [1, 1, 1]
            else:
                rectangle_color = [0, 0, 0]
                font_color = definitions.get_color_rgb_float(self.tracks_info[i]['color'])
            rectangle_height = 20
            ctx.set_source_rgb(*rectangle_color)
            ctx.rectangle(part_x, part_h - rectangle_height, w, part_h)
            ctx.fill()
            instrument_short_name = self.tracks_info[i]['instrument_short_name']
            draw_text_at(ctx, part_x + 3, part_h - 4, instrument_short_name, font_size=15, color=font_color) 

    
    def on_button_pressed(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            self.pyramid_track_selection_button_a = button_name
            self.pyramid_track_selection_button_a_pressing_time = time.time()
            self.app.buttons_need_update = True

        elif button_name in self.pyramid_track_button_names_b:
            if self.pyramid_track_selection_button_a:
                self.select_pyramid_track(self.pyramid_track_button_names_a.index(
                    self.pyramid_track_selection_button_a) + self.pyramid_track_button_names_b.index(button_name) * 8)
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0

    def on_button_released(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            if self.pyramid_track_selection_button_a:
                if time.time() - self.pyramid_track_selection_button_a_pressing_time < self.pyramid_track_selection_quick_press_time:
                    # Only switch to track if it was a quick press
                    self.select_pyramid_track(self.pyramid_track_button_names_a.index(button_name))
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                self.app.buttons_need_update = True
                self.app.pads_need_update = True

    def on_encoder_rotated(self, encoder_name, increment):
        encoder_num = [
            push2_python.constants.ENCODER_TRACK1_ENCODER,
            push2_python.constants.ENCODER_TRACK2_ENCODER,
            push2_python.constants.ENCODER_TRACK3_ENCODER,
            push2_python.constants.ENCODER_TRACK4_ENCODER,
            push2_python.constants.ENCODER_TRACK5_ENCODER,
            push2_python.constants.ENCODER_TRACK6_ENCODER,
            push2_python.constants.ENCODER_TRACK7_ENCODER,
            push2_python.constants.ENCODER_TRACK8_ENCODER,
        ].index(encoder_name)
        if self.active_midi_control_ccs:
            self.active_midi_control_ccs[encoder_num].update_value(increment)
