import cairo
import definitions
import push2_python


def show_title(ctx, x, h, text, color=[1, 1, 1]):
    text = str(text)
    ctx.set_source_rgb(*color)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    font_size = h//12
    ctx.set_font_size(font_size)
    ctx.move_to(x + 3, 20)
    ctx.show_text(text)


def show_value(ctx, x, h, text, color=[1, 1, 1]):
    text = str(text)
    ctx.set_source_rgb(*color)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    font_size = h//8
    ctx.set_font_size(font_size)
    ctx.move_to(x + 3, 45)
    ctx.show_text(text)


def draw_text_at(ctx, x, y, text, font_size = 12, color=[1, 1, 1]):
    text = str(text)
    ctx.set_source_rgb(*color)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)
    ctx.move_to(x, y)
    ctx.show_text(text)


def show_text(ctx, x_part, pixels_from_top, text, height=20, font_color=definitions.WHITE, background_color=None, margin_left=4, font_size_percentage=0.8):
    assert 0 <= x_part < 8
    assert type(x_part) == int

    display_w = push2_python.constants.DISPLAY_LINE_PIXELS
    display_h = push2_python.constants.DISPLAY_N_LINES
    part_w = display_w // 8
    x1 = part_w * x_part
    y1 = pixels_from_top

    ctx.save()

    if background_color is not None:
        ctx.set_source_rgb(*definitions.get_color_rgb_float(background_color))
        ctx.rectangle(x1, y1, part_w, y1 + height)
        ctx.fill()
    ctx.set_source_rgb(*definitions.get_color_rgb_float(font_color))
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    font_size = round(int(height * font_size_percentage))
    margin_top = (height - font_size) // 2
    ctx.set_font_size(font_size)
    ctx.move_to(x1 + margin_left, y1 + font_size + margin_top - 2)
    ctx.show_text(text)

    ctx.restore()
