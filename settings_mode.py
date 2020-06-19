import push2_python.constants
import time

from display_utils import show_title, show_value
from definitions import PyshaMode, OFF_BTN_COLOR


class SettingsMode(PyshaMode):

    # Pad settings
    # - Aftertouch mode
    # - Velocity curve
    # - Channel aftertouch range
    # - Root note

    # MIDI settings
    # - Midi device IN
    # - Midi channel IN
    # - Midi device OUT
    # - Midi channel OUT
    # - Pyramidi channel OUT
    # - MIDI monitor
    # - Rerun MIDI initial configuration?

    # About panel
    # - Version info
    # - Save current settings
    #  - FPS

    encoders_state = {}

    def initialize(self):
        current_time = time.time()
        for encoder_name in self.push.encoders.available_names:
            self.encoders_state[encoder_name] = {
                'last_message_received': current_time,
            }

    def activate(self):
        self.update_buttons()

    def deactivate(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_1, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_2, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_3, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_4, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_5, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_6, OFF_BTN_COLOR)
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_7, OFF_BTN_COLOR)

    def update_buttons(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_1, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_2, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_3, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_4, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_5, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_6, 'white')
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_UPPER_ROW_7, 'green')

    def update_display(self, ctx, w, h):

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

            if i == 0:  # MIDI in device
                if self.app.midi_in_tmp_device_idx is not None:
                    color = [1.0, 0.64, 0.0]  # Orange font
                    if self.app.midi_in_tmp_device_idx < 0:
                        name = "None"
                    else:
                        name = "{0} {1}".format(self.app.midi_in_tmp_device_idx + 1, self.app.available_midi_in_device_names[self.app.midi_in_tmp_device_idx])
                else:
                    if self.app.midi_in is not None:
                        name = "{0} {1}".format(self.app.available_midi_in_device_names.index(self.app.midi_in.name) + 1, self.app.midi_in.name)
                    else:
                        color = [0.5, 0.5, 0.5]  # Gray font
                        name = "None"
                show_title(ctx, part_x, h, 'IN DEVICE')
                show_value(ctx, part_x, h, name, color)

            elif i == 1:  # MIDI in channel
                if self.app.midi_in is None:
                    color = [0.5, 0.5, 0.5]  # Gray font
                show_title(ctx, part_x, h, 'IN CH')
                show_value(ctx, part_x, h, self.app.midi_in_channel + 1 if self.app.midi_in_channel > -1 else "All", color)

            elif i == 2:  # MIDI out device
                if self.app.midi_out_tmp_device_idx is not None:
                    color = [1.0, 0.64, 0.0]  # Orange font
                    if self.app.midi_out_tmp_device_idx < 0:
                        name = "None"
                    else:
                        name = "{0} {1}".format(self.app.midi_out_tmp_device_idx + 1, self.app.available_midi_out_device_names[self.app.midi_out_tmp_device_idx])
                else:
                    if self.app.midi_out is not None:
                        name = "{0} {1}".format(self.app.available_midi_out_device_names.index(self.app.midi_out.name) + 1, self.app.midi_out.name)
                    else:
                        color = [0.5, 0.5, 0.5]  # Gray font
                        name = "None"
                show_title(ctx, part_x, h, 'OUT DEVICE')
                show_value(ctx, part_x, h, name, color)

            elif i == 3:  # MIDI out channel
                if self.app.midi_out is None:
                    color = [0.5, 0.5, 0.5]  # Gray font
                show_title(ctx, part_x, h, 'OUT CH')
                show_value(ctx, part_x, h, self.app.midi_out_channel + 1, color)

            elif i == 4:  # Root note
                if not self.app.is_mode_active(self.app.melodic_mode):
                    color = [0.5, 0.5, 0.5]  # Gray font
                show_title(ctx, part_x, h, 'ROOT NOTE')
                show_value(ctx, part_x, h, "{0} ({1})".format(self.app.melodic_mode.note_number_to_name(
                    self.app.melodic_mode.root_midi_note), self.app.melodic_mode.root_midi_note), color)

            elif i == 5:  # Poly AT/channel AT
                show_title(ctx, part_x, h, 'AFTERTOUCH')
                show_value(ctx, part_x, h, 'polyAT' if self.app.melodic_mode.use_poly_at else 'channel', color)

            elif i == 6:  # Save button
                show_title(ctx, part_x, h, 'SAVE')
            elif i == 7:  # FPS indicator
                show_title(ctx, part_x, h, 'FPS')
                show_value(ctx, part_x, h, self.app.actual_frame_rate, color)

    def on_encoder_rotated(self, encoder_name, increment):

        self.encoders_state[encoder_name]['last_message_received'] = time.time()

        if encoder_name == push2_python.constants.ENCODER_TRACK1_ENCODER:
            if self.app.midi_in_tmp_device_idx is None:
                if self.app.midi_in is not None:
                    self.app.midi_in_tmp_device_idx = self.app.available_midi_in_device_names.index(self.app.midi_in.name)
                else:
                    self.app.midi_in_tmp_device_idx = -1
            self.app.midi_in_tmp_device_idx += increment
            if self.app.midi_in_tmp_device_idx >= len(self.app.available_midi_in_device_names):
                self.app.midi_in_tmp_device_idx = len(self.app.available_midi_in_device_names) - 1
            elif self.app.midi_in_tmp_device_idx < -1:
                self.app.midi_in_tmp_device_idx = -1  # Will use -1 for "None"

        elif encoder_name == push2_python.constants.ENCODER_TRACK2_ENCODER:
            self.app.set_midi_in_channel(self.app.midi_in_channel + increment, wrap=False)

        elif encoder_name == push2_python.constants.ENCODER_TRACK3_ENCODER:
            if self.app.midi_out_tmp_device_idx is None:
                if self.app.midi_out is not None:
                    self.app.midi_out_tmp_device_idx = self.app.available_midi_out_device_names.index(self.app.midi_out.name)
                else:
                    self.app.midi_out_tmp_device_idx = -1
            self.app.midi_out_tmp_device_idx += increment
            if self.app.midi_out_tmp_device_idx >= len(self.app.available_midi_out_device_names):
                self.app.midi_out_tmp_device_idx = len(self.app.available_midi_out_device_names) - 1
            elif self.app.midi_out_tmp_device_idx < -1:
                self.app.midi_out_tmp_device_idx = -1  # Will use -1 for "None"

        elif encoder_name == push2_python.constants.ENCODER_TRACK4_ENCODER:
            self.app.set_midi_out_channel(self.app.midi_out_channel + increment, wrap=False)

        elif encoder_name == push2_python.constants.ENCODER_TRACK5_ENCODER:
            self.app.melodic_mode.set_root_midi_note(self.app.melodic_mode.root_midi_note + increment)
            self.app.pads_need_update = True  # Using async update method because we don't really need immediate response here

        elif encoder_name == push2_python.constants.ENCODER_TRACK6_ENCODER:
            if increment >= 3:  # Only respond to "big" increments
                if not self.app.melodic_mode.use_poly_at:
                    self.app.melodic_mode.use_poly_at = True
                    self.app.push.pads.set_polyphonic_aftertouch()
            elif increment <= -3:
                if self.app.melodic_mode.use_poly_at:
                    self.app.melodic_mode.use_poly_at = False
                    self.app.push.pads.set_channel_aftertouch()

    def on_button_pressed(self, button_name):

        if button_name == push2_python.constants.BUTTON_UPPER_ROW_1:
            if self.app.midi_in_tmp_device_idx is None:
                if self.app.midi_in is not None:
                    self.app.midi_in_tmp_device_idx = self.app.available_midi_in_device_names.index(self.app.midi_in.name)
                else:
                    self.app.midi_in_tmp_device_idx = -1
            self.app.midi_in_tmp_device_idx += 1
            # Make index position wrap
            if self.app.midi_in_tmp_device_idx >= len(self.app.available_midi_in_device_names):
                self.app.midi_in_tmp_device_idx = -1  # Will use -1 for "None"
            elif self.app.midi_in_tmp_device_idx < -1:
                self.app.midi_in_tmp_device_idx = len(self.app.available_midi_in_device_names) - 1

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_2:
            self.app.set_midi_in_channel(self.app.midi_in_channel + 1, wrap=True)

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_3:
            if self.app.midi_out_tmp_device_idx is None:
                if self.app.midi_out is not None:
                    self.app.midi_out_tmp_device_idx = self.app.available_midi_out_device_names.index(self.app.midi_out.name)
                else:
                    self.app.midi_out_tmp_device_idx = -1
            self.app.midi_out_tmp_device_idx += 1
            # Make index position wrap
            if self.app.midi_out_tmp_device_idx >= len(self.app.available_midi_out_device_names):
                self.app.midi_out_tmp_device_idx = -1  # Will use -1 for "None"
            elif self.app.midi_out_tmp_device_idx < -1:
                self.app.midi_out_tmp_device_idx = len(self.app.available_midi_out_device_names) - 1

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_4:
            self.app.set_midi_out_channel(self.app.midi_out_channel + 1, wrap=True)

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_5:
            self.app.melodic_mode.set_root_midi_note(self.app.melodic_mode.root_midi_note + 1)
            self.app.pads_need_update = True

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_6:
            self.app.melodic_mode.use_poly_at = not self.app.melodic_mode.use_poly_at
            if self.app.melodic_mode.use_poly_at:
                self.app.push.pads.set_polyphonic_aftertouch()
            else:
                self.app.push.pads.set_channel_aftertouch()

        elif button_name == push2_python.constants.BUTTON_UPPER_ROW_7:
            # Save current settings
            self.app.save_current_settings_to_file()
