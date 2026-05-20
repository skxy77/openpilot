import pyray as rl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.hardware import HARDWARE
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

FONT_SIZE = 18
PADDING = 4
BG_COLOR = rl.Color(0, 0, 0, 180)
TEXT_COLOR = rl.Color(255, 200, 50, 230)
UPDATE_TEXT = "Update ready"

BTN_TEXT = "Reboot"
BTN_FONT_SIZE = 16
BTN_COLOR = rl.Color(255, 255, 255, 230)
BTN_COLOR_PRESSED = rl.Color(200, 200, 200, 230)
BTN_TEXT_COLOR = rl.BLACK
BTN_GAP = 4
BTN_H_PAD = 8

LATER_TEXT = "Later"
LATER_COLOR = rl.Color(100, 100, 100, 230)
LATER_COLOR_PRESSED = rl.Color(70, 70, 70, 230)
LATER_TEXT_COLOR = rl.WHITE


class UpdateIndicator(Widget):
  def __init__(self):
    super().__init__()
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._update_available = False
    self._dismissed = False
    self._check_counter = 99
    self._btn_rect = rl.Rectangle(0, 0, 0, 0)
    self._btn_pressed = False
    self._later_rect = rl.Rectangle(0, 0, 0, 0)
    self._later_pressed = False

  def _render(self, rect: rl.Rectangle) -> None:
    self._check_counter += 1
    if self._check_counter >= 100:
      self._check_counter = 0
      self._update_available = ui_state.params.get_bool("UpdateAvailable")

    if not self._update_available or self._dismissed:
      return

    text_size = measure_text_cached(self._font, UPDATE_TEXT, FONT_SIZE)
    btn_text_size = measure_text_cached(self._font, BTN_TEXT, BTN_FONT_SIZE)
    later_text_size = measure_text_cached(self._font, LATER_TEXT, BTN_FONT_SIZE)

    # Position at bottom-left (aligned with DMoji top-left offset)
    x = rect.x + 16
    y = rect.y + rect.height - FONT_SIZE - PADDING * 3

    # Draw text background
    bg_rect = rl.Rectangle(x - PADDING, y - PADDING, text_size.x + PADDING * 2, FONT_SIZE + PADDING * 2)
    rl.draw_rectangle_rounded(bg_rect, 0.3, 10, BG_COLOR)

    # Draw text
    rl.draw_text_ex(self._font, UPDATE_TEXT, rl.Vector2(x, y), FONT_SIZE, 0, TEXT_COLOR)

    # Draw reboot button right of the text
    btn_w = btn_text_size.x + BTN_H_PAD * 2
    btn_h = FONT_SIZE + PADDING * 2
    btn_x = bg_rect.x + bg_rect.width + BTN_GAP
    btn_y = y - PADDING
    self._btn_rect = rl.Rectangle(btn_x, btn_y, btn_w, btn_h)

    btn_color = BTN_COLOR_PRESSED if self._btn_pressed else BTN_COLOR
    rl.draw_rectangle_rounded(self._btn_rect, 0.3, 10, btn_color)

    btn_text_x = btn_x + (btn_w - btn_text_size.x) / 2
    btn_text_y = btn_y + (btn_h - btn_text_size.y) / 2
    rl.draw_text_ex(self._font, BTN_TEXT, rl.Vector2(btn_text_x, btn_text_y), BTN_FONT_SIZE, 0, BTN_TEXT_COLOR)

    # Draw "Later" button right of reboot
    later_w = later_text_size.x + BTN_H_PAD * 2
    later_x = btn_x + btn_w + BTN_GAP
    self._later_rect = rl.Rectangle(later_x, btn_y, later_w, btn_h)

    later_color = LATER_COLOR_PRESSED if self._later_pressed else LATER_COLOR
    rl.draw_rectangle_rounded(self._later_rect, 0.3, 10, later_color)

    later_text_x = later_x + (later_w - later_text_size.x) / 2
    later_text_y = btn_y + (btn_h - later_text_size.y) / 2
    rl.draw_text_ex(self._font, LATER_TEXT, rl.Vector2(later_text_x, later_text_y), BTN_FONT_SIZE, 0, LATER_TEXT_COLOR)

  def _handle_mouse_press(self, mouse_pos) -> None:
    if not self._update_available or self._dismissed:
      return
    pos = rl.Vector2(mouse_pos.x, mouse_pos.y)
    if rl.check_collision_point_rec(pos, self._btn_rect):
      self._btn_pressed = True
    elif rl.check_collision_point_rec(pos, self._later_rect):
      self._later_pressed = True

  def _handle_mouse_release(self, mouse_pos) -> None:
    pos = rl.Vector2(mouse_pos.x, mouse_pos.y)
    if self._btn_pressed and rl.check_collision_point_rec(pos, self._btn_rect):
      HARDWARE.reboot()
    if self._later_pressed and rl.check_collision_point_rec(pos, self._later_rect):
      self._dismissed = True
    self._btn_pressed = False
    self._later_pressed = False
