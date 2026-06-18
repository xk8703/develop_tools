"""生成工具箱应用图标 - { } 齿轮风格"""
from PIL import Image, ImageDraw
import math


def create_icon(size=256):
    # === 深蓝渐变圆角背景 ===
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        ratio = y / size
        r = int(30 + (18 - 30) * ratio)
        g = int(58 + (40 - 58) * ratio)
        b = int(138 + (110 - 138) * ratio)
        bg_draw.line([(0, y), (size - 1, y)], fill=(r, g, b, 255))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.22, fill=255)
    bg.putalpha(mask)
    img = bg
    draw = ImageDraw.Draw(img)
    m = size

    cx, cy = m * 0.50, m * 0.46
    brace_color = (120, 185, 255)
    brace_w = max(3, int(m * 0.028))
    brace_h = m * 0.36
    brace_top = cy - brace_h / 2
    brace_bot = cy + brace_h / 2

    # === 左大括号 { ===
    bl_x = m * 0.18  # 左端
    br_x = m * 0.30  # 右端（弯头）
    mid_y = cy
    # 上横
    draw.line([(bl_x, brace_top), (br_x, brace_top)], fill=brace_color, width=brace_w)
    # 上竖
    draw.line([(br_x, brace_top), (br_x, mid_y - m * 0.03)], fill=brace_color, width=brace_w)
    # 中横（向左伸）
    draw.line([(bl_x, mid_y), (br_x, mid_y)], fill=brace_color, width=brace_w)
    # 下竖
    draw.line([(br_x, mid_y + m * 0.03), (br_x, brace_bot)], fill=brace_color, width=brace_w)
    # 下横
    draw.line([(bl_x, brace_bot), (br_x, brace_bot)], fill=brace_color, width=brace_w)
    # 弯头弧线
    arc_r = m * 0.03
    _draw_arc(draw, bl_x, brace_top, arc_r, math.pi, math.pi * 1.5, brace_color, brace_w)
    _draw_arc(draw, bl_x, mid_y, arc_r, 0, math.pi, brace_color, brace_w)
    _draw_arc(draw, bl_x, brace_bot, arc_r, math.pi * 0.5, math.pi, brace_color, brace_w)

    # === 右大括号 } ===
    bl2_x = m * 0.70
    br2_x = m * 0.82
    # 上横
    draw.line([(bl2_x, brace_top), (br2_x, brace_top)], fill=brace_color, width=brace_w)
    # 上竖
    draw.line([(bl2_x, brace_top), (bl2_x, mid_y - m * 0.03)], fill=brace_color, width=brace_w)
    # 中横
    draw.line([(bl2_x, mid_y), (br2_x, mid_y)], fill=brace_color, width=brace_w)
    # 下竖
    draw.line([(bl2_x, mid_y + m * 0.03), (bl2_x, brace_bot)], fill=brace_color, width=brace_w)
    # 下横
    draw.line([(bl2_x, brace_bot), (br2_x, brace_bot)], fill=brace_color, width=brace_w)
    # 弯头弧线
    _draw_arc(draw, br2_x, brace_top, arc_r, math.pi * 1.5, math.pi * 2, brace_color, brace_w)
    _draw_arc(draw, br2_x, mid_y, arc_r, math.pi, math.pi * 2, brace_color, brace_w)
    _draw_arc(draw, br2_x, brace_bot, arc_r, 0, math.pi * 0.5, brace_color, brace_w)

    # === 中心金色齿轮 ===
    gcx, gcy = cx, cy
    outer_r = m * 0.18
    inner_r = m * 0.13
    gear_color = (255, 210, 70)
    _draw_gear_smooth(draw, gcx, gcy, outer_r, inner_r, 8, gear_color)
    # 齿轮中心深蓝圆
    cr = m * 0.065
    draw.ellipse([gcx - cr, gcy - cr, gcx + cr, gcy + cr], fill=(30, 58, 138))
    # 中心高光点
    hr = m * 0.028
    draw.ellipse([gcx - hr, gcy - hr, gcx + hr, gcy + hr], fill=(255, 230, 120))

    # === 底部横条装饰 ===
    bar_t = m * 0.82
    bar_b = m * 0.91
    draw.rounded_rectangle([m * 0.22, bar_t, m * 0.78, bar_b],
                           radius=m * 0.04, fill=(50, 85, 160))
    # 三个菱形装饰
    for dx in [-0.14, 0, 0.14]:
        _draw_diamond(draw, cx + m * dx, (bar_t + bar_b) / 2, m * 0.02, (120, 185, 255))

    return img


def _draw_gear_smooth(draw, cx, cy, outer_r, inner_r, teeth, color):
    """画平滑齿轮"""
    points = []
    steps_per_tooth = 12
    for i in range(teeth):
        base_angle = (i * 2 * math.pi / teeth) - math.pi / 2
        for j in range(steps_per_tooth):
            t = j / steps_per_tooth
            angle = base_angle + t * (2 * math.pi / teeth)
            phase = t
            if phase < 0.15:
                r = inner_r + (outer_r - inner_r) * (phase / 0.15)
            elif phase < 0.35:
                r = outer_r
            elif phase < 0.50:
                r = outer_r - (outer_r - inner_r) * ((phase - 0.35) / 0.15)
            else:
                r = inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
    if len(points) > 2:
        draw.polygon(points, fill=color)


def _draw_arc(draw, cx, cy, r, start_angle, end_angle, color, width):
    """用短线段画弧线"""
    steps = 6
    points = []
    for i in range(steps + 1):
        t = i / steps
        a = start_angle + t * (end_angle - start_angle)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        points.append((x, y))
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=color, width=width)


def _draw_diamond(draw, cx, cy, r, color):
    """画菱形"""
    points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    draw.polygon(points, fill=color)


if __name__ == "__main__":
    icon_256 = create_icon(256)
    icon_256.save("assets/ico/icon5.png", "PNG")
    print("icon5.png saved")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        images.append(create_icon(s))

    images[0].save("assets/ico/icon5.ico", format="ICO",
                    sizes=[(img.width, img.height) for img in images],
                    append_images=images[1:])
    print("icon5.ico saved")
