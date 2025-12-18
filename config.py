"""
Global configuration for the pygame Minesweeper game.

This module centralizes all tunable settings used by both the logic layer
(only grid sizes and counts) and the presentation layer (colors, fonts,
layout metrics). Keeping these in one place helps tweak gameplay and visuals
without touching logic or rendering code.

Groups:
- Grid and display: board dimensions, cell size, margins, derived window size
- Colors: palette for cells, numbers, flags, overlays
- Text/UI: font sizes for body, header, and result
- Input: mouse button mappings
- Behavior: highlight duration, overlay alpha
"""

# Display settings
fps = 60

# Grid settings
cols = 16
rows = 16
num_mines = 40

# Cell size and margins
cell_size = 32
margin_left = 20
margin_top = 60
margin_right = 20
margin_bottom = 20

# Derived display dimension
width = margin_left + cols * cell_size + margin_right
height = margin_top + rows * cell_size + margin_bottom

display_dimension = (width, height)

# Colors
color_bg = (24, 26, 27)
color_grid = (60, 64, 67)
color_cell_hidden = (40, 44, 52)
color_cell_revealed = (225, 228, 232)
color_cell_mine = (220, 0, 0)
flag_color_options = {
    "Red": (220,0,0),
    "Orange": (255,140,0),
    "Yellow": (255,255,0),
    "Green": (50,205,50)
}#선택 가능한 깃발 색상 리스트(빨강,주황,노랑,녹색)
color_flag = flag_color_options["Red"]#기본값(빨강)으로 변경
color_text = (20, 20, 20)
color_text_inv = (240, 240, 240)
color_header_text = (240, 240, 240)
color_header = (32, 34, 36)
color_highlight = (70, 130, 180)
color_result = (242, 242, 0)
#체크박스 UI 관련 설정
checkbox_size = 18
checkbox_gap = 70
# Number colors 1~8
number_colors = {
    1: (25, 118, 210),   # blue
    2: (56, 142, 60),    # green
    3: (211, 47, 47),    # red
    4: (123, 31, 162),   # purple
    5: (255, 143, 0),    # orange
    6: (0, 151, 167),    # cyan
    7: (85, 85, 85),     # gray
    8: (0, 0, 0),        # black
}

# Text / UI
font_name = None  # default pygame font
font_size = 22
header_font_size = 24
result_font_size = 64

# Input
mouse_left = 1
mouse_middle = 2
mouse_right = 3

# Highlight behavior (milliseconds)
highlight_duration_ms = 600

# Overlay alpha for result background (0~255)
result_overlay_alpha = 120

# Misc
title = "Minesweeper"

