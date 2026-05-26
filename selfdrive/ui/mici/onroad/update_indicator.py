import time
import threading
import pyray as rl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.hardware import HARDWARE
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

PADDING = 8

BTN_TEXT = "Restart"
BTN_FONT_SIZE = 28
BTN_COLOR = rl.Color(255, 255, 255, 230)
BTN_COLOR_PRESSED = rl.Color(200, 200, 200, 230)
BTN_TEXT_COLOR = rl.BLACK
BTN_GAP = 8
BTN_H_PAD = 16
BTN_V_PAD = 10

LATER_TEXT = "Later"
LATER_COLOR = rl.Color(100, 100, 100, 230)
LATER_COLOR_PRESSED = rl.Color(70, 70, 70, 230)
LATER_TEXT_COLOR = rl.WHITE

OFFROAD_WAIT_SECONDS = 3


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
    self._reboot_pending = False

  @staticmethod
  def _offroad_then_reboot():
    """Set OffroadMode, wait for transition, then reboot."""
    ui_state.params.put_bool("OffroadMode", True)
    time.sleep(OFFROAD_WAIT_SECONDS)
    HARDWARE.reboot()

  def _render(self, rect: rl.Rectangle) -> None:
    self._check_counter += 1
    if self._check_counter >= 100:
      self._check_counter = 0
      self._update_available = ui_state.params.get_bool("UpdateAvailable")

    if not self._update_available or self._dismissed or self._reboot_pending:
      return

    btn_text_size = measure_text_cached(self._font, BTN_TEXT, BTN_FONT_SIZE)
    later_text_size = measure_text_cached(self._font, LATER_TEXT, BTN_FONT_SIZE)

    # Position at bottom-right
    btn_h = BTN_FONT_SIZE + BTN_V_PAD * 2
    btn_w = btn_text_size.x + BTN_H_PAD * 2
    later_w = later_text_size.x + BTN_H_PAD * 2
    total_w = btn_w + BTN_GAP + later_w
    x = rect.x + rect.width - total_w - 16
    btn_y = rect.y + rect.height - btn_h - PADDING

    # Draw restart button
    self._btn_rect = rl.Rectangle(x, btn_y, btn_w, btn_h)

    btn_color = BTN_COLOR_PRESSED if self._btn_pressed else BTN_COLOR
    rl.draw_rectangle_rounded(self._btn_rect, 0.3, 10, btn_color)

    btn_text_x = x + (btn_w - btn_text_size.x) / 2
    btn_text_y = btn_y + (btn_h - btn_text_size.y) / 2
    rl.draw_text_ex(self._font, BTN_TEXT, rl.Vector2(btn_text_x, btn_text_y), BTN_FONT_SIZE, 0, BTN_TEXT_COLOR)

    # Draw "Later" button right of restart
    later_x = x + btn_w + BTN_GAP
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
      if not self._reboot_pending:
        self._reboot_pending = True
        threading.Thread(target=self._offroad_then_reboot, daemon=True).start()
    if self._later_pressed and rl.check_collision_point_rec(pos, self._later_rect):
      self._dismissed = True
    self._btn_pressed = False
    self._later_pressed = False
