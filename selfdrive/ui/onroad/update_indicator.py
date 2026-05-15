import pyray as rl
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

FONT_SIZE = 38
PADDING = 12
BG_COLOR = rl.Color(0, 0, 0, 180)
TEXT_COLOR = rl.Color(255, 200, 50, 230)
UPDATE_TEXT = "Update pending reboot"


class UpdateIndicator(Widget):
  def __init__(self):
    super().__init__()
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._update_available = False
    self._check_counter = 0

  def _render(self, rect: rl.Rectangle) -> None:
    # Check param every ~100 frames to avoid I/O overhead
    self._check_counter += 1
    if self._check_counter >= 100:
      self._check_counter = 0
      self._update_available = ui_state.params.get_bool("UpdateAvailable")

    if not self._update_available:
      return

    text_size = measure_text_cached(self._font, UPDATE_TEXT, FONT_SIZE)

    # Position at bottom-left of the content rect
    x = rect.x + UI_BORDER_SIZE + PADDING
    y = rect.y + rect.height - UI_BORDER_SIZE - FONT_SIZE - PADDING * 2

    # Draw background rounded rectangle
    bg_rect = rl.Rectangle(x - PADDING, y - PADDING, text_size.x + PADDING * 2, FONT_SIZE + PADDING * 2)
    rl.draw_rectangle_rounded(bg_rect, 0.3, 10, BG_COLOR)

    # Draw text
    rl.draw_text_ex(self._font, UPDATE_TEXT, rl.Vector2(x, y), FONT_SIZE, 0, TEXT_COLOR)
