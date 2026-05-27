import time
import pyray as rl
from cereal import log
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget

NetworkType = log.DeviceState.NetworkType

ICON_SIZE = 44
PADDING = 16
BG_COLOR = rl.Color(0, 0, 0, 140)
ICON_COLOR = rl.WHITE


class WifiIndicator(Widget):
  """Shows a WiFi icon at bottom-right when connected to WiFi with internet."""

  def __init__(self):
    super().__init__()
    self._wifi_icon = gui_app.texture("icons/wifi_strength_full.png", ICON_SIZE, ICON_SIZE)
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

    # Position at bottom-left, matching DMoji visual edge padding (10px)
    # The background circle extends beyond the icon bounds, so offset to compensate
    bg_radius = ICON_SIZE * 0.7
    bg_overhang = bg_radius - ICON_SIZE / 2
    x = rect.x + 10 + bg_overhang
    y = rect.y + rect.height - ICON_SIZE - 10 - bg_overhang

    # Draw background circle
    center_x = x + ICON_SIZE / 2
    center_y = y + ICON_SIZE / 2
    rl.draw_circle(int(center_x), int(center_y), ICON_SIZE * 0.7, BG_COLOR)

    # Draw WiFi icon
    rl.draw_texture_ex(self._wifi_icon, rl.Vector2(x, y), 0.0, 1.0, ICON_COLOR)
