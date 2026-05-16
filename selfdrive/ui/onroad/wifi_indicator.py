import time
import pyray as rl
from cereal import log
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.widgets import Widget

NetworkType = log.DeviceState.NetworkType

ICON_SIZE = 48
BADGE_SIZE = 20
BADGE_FONT_SIZE = 16
PADDING = 16
BG_COLOR = rl.Color(0, 0, 0, 140)
ICON_COLOR = rl.WHITE
BADGE_BG = rl.Color(22, 127, 64, 230)
BADGE_TEXT_COLOR = rl.WHITE


class WifiIndicator(Widget):
  """Shows a WiFi icon at bottom-right when connected to WiFi with internet."""

  def __init__(self):
    super().__init__()
    self._wifi_icon = gui_app.texture("icons/wifi_strength_full.png", ICON_SIZE, ICON_SIZE)
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._is_wifi = False
    self._has_internet = False

  def _update_state(self):
    sm = ui_state.sm
    if not sm.updated['deviceState']:
      return

    device_state = sm['deviceState']
    self._is_wifi = device_state.networkType == NetworkType.wifi

    last_ping = device_state.lastAthenaPingTime
    if last_ping == 0:
      self._has_internet = False
    else:
      self._has_internet = (time.monotonic_ns() - last_ping) < 80_000_000_000  # 80 seconds

  def _render(self, rect: rl.Rectangle) -> None:
    if not (self._is_wifi and self._has_internet):
      return

    # Position at bottom-right
    x = rect.x + rect.width - ICON_SIZE - PADDING * 2
    y = rect.y + rect.height - ICON_SIZE - PADDING * 2

    # Draw background circle
    center_x = x + ICON_SIZE / 2
    center_y = y + ICON_SIZE / 2
    rl.draw_circle(int(center_x), int(center_y), ICON_SIZE * 0.7, BG_COLOR)

    # Draw WiFi icon
    rl.draw_texture_ex(self._wifi_icon, rl.Vector2(x, y), 0.0, 1.0, ICON_COLOR)

    # Draw small "1" badge at top-right of the icon
    badge_x = x + ICON_SIZE - BADGE_SIZE / 2
    badge_y = y - BADGE_SIZE / 4
    rl.draw_circle(int(badge_x), int(badge_y), BADGE_SIZE / 2, BADGE_BG)
    rl.draw_text_ex(self._font, "1", rl.Vector2(badge_x - 4, badge_y - BADGE_FONT_SIZE / 2), BADGE_FONT_SIZE, 0, BADGE_TEXT_COLOR)
