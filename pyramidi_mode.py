import definitions
import mido
import push2_python
import time
import math

from definitions import PyshaMode, OFF_BTN_COLOR, LAYOUT_MELODIC, LAYOUT_RHYTHMIC, PYRAMIDI_CHANNEL
from display_utils import draw_text_at, show_title, show_value, show_text


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

    def draw(self, ctx, x_part):
        margin_top = 25
        
        # Param name
        name_height = 20
        show_text(ctx, x_part, margin_top, self.name, height=name_height, font_color=definitions.WHITE)

        # Param value
        val_height = 30
        color = self.get_color_func()
        show_text(ctx, x_part, margin_top + name_height, str(self.value), height=val_height, font_color=color)

        # Knob
        ctx.save()

        circle_break_degrees = 80
        height = 55
        radius = height/2

        display_w = push2_python.constants.DISPLAY_LINE_PIXELS
        x = (display_w // 8) * x_part
        y = margin_top + name_height + val_height + radius + 5
        
        start_rad = (90 + circle_break_degrees // 2) * (math.pi / 180)
        end_rad = (90 - circle_break_degrees // 2) * (math.pi / 180)
        xc = x + radius + 3
        yc = y

        def get_rad_for_value(value):
            total_degrees = 360 - circle_break_degrees
            return start_rad + total_degrees * ((value - self.vmin)/(self.vmax - self.vmin)) * (math.pi / 180)

        # This is needed to prevent showing line from previous position
        ctx.set_source_rgb(0, 0, 0)
        ctx.move_to(xc, yc)
        ctx.stroke()

        # Inner circle
        ctx.arc(xc, yc, radius, start_rad, end_rad)
        ctx.set_source_rgb(*definitions.get_color_rgb_float(definitions.GRAY_LIGHT))
        ctx.set_line_width(1)
        ctx.stroke()

        # Outer circle
        ctx.arc(xc, yc, radius, start_rad, get_rad_for_value(self.value))
        ctx.set_source_rgb(* definitions.get_color_rgb_float(color))
        ctx.set_line_width(3)
        ctx.stroke()

        ctx.restore()
    
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

    midi_cc_button_names = [
        push2_python.constants.BUTTON_UPPER_ROW_1,
        push2_python.constants.BUTTON_UPPER_ROW_2,
        push2_python.constants.BUTTON_UPPER_ROW_3,
        push2_python.constants.BUTTON_UPPER_ROW_4,
        push2_python.constants.BUTTON_UPPER_ROW_5,
        push2_python.constants.BUTTON_UPPER_ROW_6,
        push2_python.constants.BUTTON_UPPER_ROW_7,
        push2_python.constants.BUTTON_UPPER_ROW_8
    ]
    synth_midi_control_ccs = {}
    active_midi_control_ccs = []
    current_selected_section_and_page = {}

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

        # Create MIDI CC mappings for synths with definitions
        for synth_name, data in synth_midi_control_cc_data.items():
            self.synth_midi_control_ccs[synth_name] = []
            for section in data:
                section_name = section['section']
                for name, cc_number in section['controls']:
                    control = MIDICCControl(cc_number, name, section_name, self.get_current_track_color, self.app.send_midi)
                    self.synth_midi_control_ccs[synth_name].append(control)

        # Create MIDI CC mappings for synths without definitions
        for synth_name in list(set([track['instrument_short_name'] for track in self.tracks_info])):
            if synth_name not in self.synth_midi_control_ccs:
                self.synth_midi_control_ccs[synth_name] = []
                for i in range(0, 128):
                    section_s = (i // 16) * 16
                    section_e = section_s + 16
                    control = MIDICCControl(i, 'CC {0}'.format(i), '{0} to {1}'.format(section_s, section_e), self.get_current_track_color, self.app.send_midi)
                    self.synth_midi_control_ccs[synth_name].append(control)

        # Fill in current page and section variables
        for synth_name in self.synth_midi_control_ccs:
            self.current_selected_section_and_page[synth_name] = (self.synth_midi_control_ccs[synth_name][0].section, 0)
        
        self.select_pyramid_track(self.selected_pyramid_track)

    def get_current_track_instrument_short_name(self):
        return self.tracks_info[self.selected_pyramid_track]['instrument_short_name']

    def get_current_track_color(self):
        return self.tracks_info[self.selected_pyramid_track]['color']

    def get_current_track_color_rgb(self):
        return definitions.get_color_rgb_float(self.get_current_track_color())

    def get_current_track_midi_cc_sections(self):
        section_names = []
        for control in self.synth_midi_control_ccs.get(self.get_current_track_instrument_short_name(), []):
            section_name = control.section
            if section_name not in section_names:
                section_names.append(section_name)
        return section_names

    def get_currently_selected_midi_cc_section_and_page(self):
        return self.current_selected_section_and_page[self.get_current_track_instrument_short_name()]

    def get_midi_cc_controls_for_current_track_and_section(self):
        section, _ = self.get_currently_selected_midi_cc_section_and_page()
        return [control for control in self.synth_midi_control_ccs.get(self.get_current_track_instrument_short_name(), []) if control.section == section]

    def get_midi_cc_controls_for_current_track_section_and_page(self):
        all_section_controls = self.get_midi_cc_controls_for_current_track_and_section()
        _, page = self.get_currently_selected_midi_cc_section_and_page()
        try:
            return all_section_controls[page * 8:(page+1) * 8]
        except IndexError:
            return []

    def update_current_section_page(self, new_section=None, new_page=None):
        current_section, current_page = self.get_currently_selected_midi_cc_section_and_page()
        result = [current_section, current_page]
        if new_section is not None:
            result[0] = new_section
        if new_page is not None:
            result[1] = new_page
        self.current_selected_section_and_page[self.get_current_track_instrument_short_name()] = result
        self.active_midi_control_ccs = self.get_midi_cc_controls_for_current_track_section_and_page()
        self.app.buttons_need_update = True

    def get_should_show_midi_cc_next_prev_pages_for_section(self):
        all_section_controls = self.get_midi_cc_controls_for_current_track_and_section()
        _, page = self.get_currently_selected_midi_cc_section_and_page()
        show_prev = False
        if page > 0:
            show_prev = True
        show_next = False
        if (page + 1) * 8 < len(all_section_controls):
            show_next = True
        return show_prev, show_next
        
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
        self.active_midi_control_ccs = self.get_midi_cc_controls_for_current_track_section_and_page()

    def activate(self):
        self.update_buttons()

    def deactivate(self):
        for button_name in self.pyramid_track_button_names_a + self.pyramid_track_button_names_b + self.midi_cc_button_names:
            self.push.buttons.set_button_color(button_name, definitions.BLACK)

    def update_buttons(self):
        for count, name in enumerate(self.pyramid_track_button_names_a):
            color = self.tracks_info[count]['color']
            self.push.buttons.set_button_color(name, color)

        for count, name in enumerate(self.pyramid_track_button_names_b):
            if self.pyramid_track_selection_button_a:
                color = self.tracks_info[self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a)]['color']
                equivalent_track_num = self.pyramid_track_button_names_a.index(self.pyramid_track_selection_button_a) + count * 8
                if self.selected_pyramid_track == equivalent_track_num:
                    self.push.buttons.set_button_color(name, definitions.WHITE)
                    self.push.buttons.set_button_color(name, color, animation=definitions.DEFAULT_ANIMATION)
                else:
                    self.push.buttons.set_button_color(name, color)
            else:
                color = self.get_current_track_color()
                equivalent_track_num = (self.selected_pyramid_track % 8) + count * 8
                if self.selected_pyramid_track == equivalent_track_num:
                    self.push.buttons.set_button_color(name, definitions.WHITE)
                    self.push.buttons.set_button_color(name, color, animation=definitions.DEFAULT_ANIMATION)
                else:
                    self.push.buttons.set_button_color(name, color)

        n_midi_cc_sections = len(self.get_current_track_midi_cc_sections())
        for count, name in enumerate(self.midi_cc_button_names):
            if count < n_midi_cc_sections:
                self.push.buttons.set_button_color(name, definitions.WHITE)
            else:
                self.push.buttons.set_button_color(name, definitions.OFF_BTN_COLOR)

        show_prev, show_next = self.get_should_show_midi_cc_next_prev_pages_for_section()
        if show_prev:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_PAGE_LEFT, definitions.WHITE)
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_PAGE_LEFT, definitions.BLACK)
        if show_next:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_PAGE_RIGHT, definitions.WHITE)
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_PAGE_RIGHT, definitions.BLACK)

    def update_display(self, ctx, w, h):

        # Draw MIDI CCs section names
        section_names = self.get_current_track_midi_cc_sections()[0:8]
        if section_names:
            height = 20
            for i, section_name in enumerate(section_names):
                show_text(ctx, i, 0, section_name, background_color=definitions.RED)
                
                is_selected = False
                selected_section, _ = self.get_currently_selected_midi_cc_section_and_page()
                if selected_section == section_name:
                    is_selected = True

                if is_selected:
                    background_color = self.get_current_track_color()
                    font_color = definitions.BLACK
                else:
                    background_color = definitions.BLACK
                    font_color = self.get_current_track_color()
                show_text(ctx, i, 0, section_name, height=height,
                        font_color=font_color, background_color=background_color)

        # Draw MIDI CC controls
        if self.active_midi_control_ccs:
            for i in range(0, min(len(self.active_midi_control_ccs), 8)):
                try:
                    self.active_midi_control_ccs[i].draw(ctx, i)
                except IndexError:
                    continue

        # Draw track selector labels
        height = 20
        for i in range(0, 8):
            if self.selected_pyramid_track % 8 == i:
                background_color = self.tracks_info[i]['color']
                font_color = definitions.BLACK
            else:
                background_color = definitions.BLACK
                font_color = self.tracks_info[i]['color']
            instrument_short_name = self.tracks_info[i]['instrument_short_name']
            show_text(ctx, i, h - height, instrument_short_name, height=height,
                      font_color=font_color, background_color=background_color)
 
    
    def on_button_pressed(self, button_name):
        if button_name in self.pyramid_track_button_names_a:
            self.pyramid_track_selection_button_a = button_name
            self.pyramid_track_selection_button_a_pressing_time = time.time()
            self.app.buttons_need_update = True
            return True

        elif button_name in self.pyramid_track_button_names_b:
            if self.pyramid_track_selection_button_a:
                # While pressing one of the track selection a buttons
                self.select_pyramid_track(self.pyramid_track_button_names_a.index(
                    self.pyramid_track_selection_button_a) + self.pyramid_track_button_names_b.index(button_name) * 8)
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                self.pyramid_track_selection_button_a = False
                self.pyramid_track_selection_button_a_pressing_time = 0
                return True
            else:
                # No track selection a button being pressed...
                self.select_pyramid_track(self.selected_pyramid_track % 8 + 8 * self.pyramid_track_button_names_b.index(button_name))
                self.app.buttons_need_update = True
                self.app.pads_need_update = True
                return True

        elif button_name in self.midi_cc_button_names:
            current_track_sections = self.get_current_track_midi_cc_sections()
            n_sections = len(current_track_sections)
            idx = self.midi_cc_button_names.index(button_name)
            if idx < n_sections:
                new_section = current_track_sections[idx]
                self.update_current_section_page(new_section=new_section)
            return True

        elif button_name in [push2_python.constants.BUTTON_PAGE_LEFT, push2_python.constants.BUTTON_PAGE_RIGHT]:
            show_prev, show_next = self.get_should_show_midi_cc_next_prev_pages_for_section()
            _, current_page = self.get_currently_selected_midi_cc_section_and_page()
            if button_name == push2_python.constants.BUTTON_PAGE_LEFT and show_prev:
                self.update_current_section_page(new_page=current_page - 1)
            elif button_name == push2_python.constants.BUTTON_PAGE_RIGHT and show_next:
                self.update_current_section_page(new_page=current_page + 1)
            return True


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
                return True


    def on_encoder_rotated(self, encoder_name, increment):
        try:
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
        except ValueError: 
            pass  # Encoder not in list 
        return True  # Always return True because encoder should not be used in any other mode if this is first active
