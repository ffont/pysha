import push2_python

from melodic_mode import MelodicMode


class RhythmicMode(MelodicMode):

    rhythmic_notes_matrix = [
        [64, 65, 66, 67, 96, 97, 98, 99],
        [60, 61, 62, 63, 92, 93, 94, 95],
        [56, 57, 58, 59, 88, 89, 90, 91],
        [52, 53, 54, 55, 84, 85, 86, 87],
        [48, 49, 50, 51, 80, 81, 82, 83],
        [44, 45, 46, 47, 76, 77, 78, 79],
        [40, 41, 42, 43, 72, 73, 74, 75],
        [36, 37, 38, 39, 68, 69, 70, 71]
    ]

    def pad_ij_to_midi_note(self, pad_ij):
        return self.rhythmic_notes_matrix[pad_ij[0]][pad_ij[1]]

    def deactivate(self):
        self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, 'black')

    def update_buttons(self):
        if self.fixed_velocity_mode:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, 'white')
        else:
            self.push.buttons.set_button_color(push2_python.constants.BUTTON_ACCENT, 'dark_gray')

    def update_pads(self):
        color_matrix = []
        for i in range(0, 8):
            row_colors = []
            for j in range(0, 8):
                corresponding_midi_note = self.pad_ij_to_midi_note([i, j])
                cell_color = 'black'
                if i >= 4 and j < 4:
                    if not self.fixed_velocity_mode:
                        cell_color = 'yellow'
                    else:
                        cell_color = 'blue'
                elif i >= 4 and j >= 4:
                    cell_color = 'turquoise'
                elif i < 4 and j < 4:
                    cell_color = 'orange'
                elif i < 4 and j >= 4:
                    cell_color = 'pink'
                if self.is_midi_note_being_played(corresponding_midi_note):
                    cell_color = 'green'

                row_colors.append(cell_color)
            color_matrix.append(row_colors)

        self.push.pads.set_pads_color(color_matrix)

    def on_button_pressed(self, button_name):
        if button_name == push2_python.constants.BUTTON_ACCENT:
            self.fixed_velocity_mode = not self.fixed_velocity_mode
            self.buttons_need_update = True
            self.app.pads_need_update = True
