import datetime
import os
import time
import threading

from cereal import log
import pyray as rl
from collections.abc import Callable
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.layouts import HBoxLayout
from openpilot.system.ui.widgets.icon_widget import IconWidget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.lib.application import gui_app, FontWeight, MousePos
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.hardware import HARDWARE
from openpilot.system.version import RELEASE_BRANCHES

HEAD_BUTTON_FONT_SIZE = 40
HOME_PADDING = 8

NetworkType = log.DeviceState.NetworkType

NETWORK_TYPES = {
  NetworkType.none: "Offline",
  NetworkType.wifi: "WiFi",
  NetworkType.cell2G: "2G",
  NetworkType.cell3G: "3G",
  NetworkType.cell4G: "LTE",
  NetworkType.cell5G: "5G",
  NetworkType.ethernet: "Ethernet",
}


class NetworkIcon(Widget):
  def __init__(self):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, 54, 44))  # max size of all icons
    self._net_type = NetworkType.none
    self._net_strength = 0

    self._wifi_slash_txt = gui_app.texture("icons_mici/settings/network/wifi_strength_slash.png", 50, 44)
    self._wifi_none_txt = gui_app.texture("icons_mici/settings/network/wifi_strength_none.png", 50, 37)
    self._wifi_low_txt = gui_app.texture("icons_mici/settings/network/wifi_strength_low.png", 50, 37)
    self._wifi_medium_txt = gui_app.texture("icons_mici/settings/network/wifi_strength_medium.png", 50, 37)
    self._wifi_full_txt = gui_app.texture("icons_mici/settings/network/wifi_strength_full.png", 50, 37)

    self._cell_none_txt = gui_app.texture("icons_mici/settings/network/cell_strength_none.png", 54, 36)
    self._cell_low_txt = gui_app.texture("icons_mici/settings/network/cell_strength_low.png", 54, 36)
    self._cell_medium_txt = gui_app.texture("icons_mici/settings/network/cell_strength_medium.png", 54, 36)
    self._cell_high_txt = gui_app.texture("icons_mici/settings/network/cell_strength_high.png", 54, 36)
    self._cell_full_txt = gui_app.texture("icons_mici/settings/network/cell_strength_full.png", 54, 36)

  def _update_state(self):
    device_state = ui_state.sm['deviceState']
    self._net_type = device_state.networkType
    strength = device_state.networkStrength
    self._net_strength = max(0, min(5, strength.raw + 1)) if strength.raw > 0 else 0

  def _render(self, _):
    if self._net_type == NetworkType.wifi:
      # There is no 1
      draw_net_txt = {0: self._wifi_none_txt,
                      2: self._wifi_low_txt,
                      3: self._wifi_medium_txt,
                      4: self._wifi_full_txt,
                      5: self._wifi_full_txt}.get(self._net_strength, self._wifi_low_txt)
    elif self._net_type in (NetworkType.cell2G, NetworkType.cell3G, NetworkType.cell4G, NetworkType.cell5G):
      draw_net_txt = {0: self._cell_none_txt,
                      2: self._cell_low_txt,
                      3: self._cell_medium_txt,
                      4: self._cell_high_txt,
                      5: self._cell_full_txt}.get(self._net_strength, self._cell_none_txt)
    else:
      draw_net_txt = self._wifi_slash_txt

    draw_x = self._rect.x + (self._rect.width - draw_net_txt.width) / 2
    draw_y = self._rect.y + (self._rect.height - draw_net_txt.height) / 2

    if draw_net_txt == self._wifi_slash_txt:
      # Offset by difference in height between slashless and slash icons to make center align match
      draw_y -= (self._wifi_slash_txt.height - self._wifi_none_txt.height) / 2

    rl.draw_texture_ex(draw_net_txt, rl.Vector2(draw_x, draw_y), 0.0, 1.0, rl.Color(255, 255, 255, int(255 * 0.9)))


class ForceOnroadIcon(Widget):
  """Small icon indicator for force onroad state."""
  SIZE = 48

  def __init__(self):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, self.SIZE, self.SIZE))
    self.set_enabled(False)
    self._active = False
    self._texture = gui_app.texture("icons_mici/wheel.png", 48, 48)

  def set_active(self, active: bool):
    self._active = active

  def _render(self, _) -> None:
    color = rl.Color(0, 220, 0, 230) if self._active else rl.Color(150, 150, 150, 120)
    rl.draw_texture_ex(self._texture, rl.Vector2(self._rect.x, self._rect.y), 0.0, 1.0, color)


class UpdateIcon(Widget):
  """Small icon button to trigger update download + auto-reboot."""
  SIZE = 48

  def __init__(self):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, self.SIZE, self.SIZE))
    self.set_enabled(False)
    self._updating = False
    self._texture = gui_app.texture("icons_mici/settings/device/update.png", 48, 48)

  @property
  def updating(self) -> bool:
    return self._updating

  def set_updating(self, updating: bool):
    self._updating = updating

  def _render(self, _) -> None:
    # Draw icon centered with color tint to indicate state
    icon_x = self._rect.x + (self.SIZE - self._texture.width) / 2
    icon_y = self._rect.y + (self.SIZE - self._texture.height) / 2
    if self._updating:
      alpha = int(150 + 70 * abs(((rl.get_time() * 2) % 2) - 1))
      color = rl.Color(100, 180, 255, alpha)
    else:
      color = rl.Color(255, 200, 0, 230)
    rl.draw_texture_ex(self._texture, rl.Vector2(icon_x, icon_y), 0.0, 1.0, color)


class MiciHomeLayout(Widget):
  def __init__(self):
    super().__init__()
    self._on_settings_click: Callable | None = None

    self._last_refresh = 0
    self._mouse_down_t: None | float = None
    self._did_long_press = False
    self._is_pressed_prev = False

    self._version_text = None
    self._experimental_mode = False
    self._force_onroad = False
    self._update_in_progress = False

    self._experimental_icon = IconWidget("icons_mici/experimental_mode.png", (48, 48))
    self._mic_icon = IconWidget("icons_mici/microphone.png", (32, 46))
    self._force_onroad_icon = ForceOnroadIcon()
    self._update_icon = UpdateIcon()

    self._status_bar_layout = HBoxLayout([
      IconWidget("icons_mici/settings.png", (48, 48), opacity=0.9),
      NetworkIcon(),
      self._force_onroad_icon,
      self._update_icon,
      self._experimental_icon,
      self._mic_icon,
    ], spacing=18)

    self._openpilot_label = UnifiedLabel("sunnypilot", font_size=96, font_weight=FontWeight.DISPLAY, max_width=480, wrap_text=False)
    self._version_label = UnifiedLabel("", font_size=36, font_weight=FontWeight.ROMAN, max_width=480, wrap_text=False)
    self._large_version_label = UnifiedLabel("", font_size=64, text_color=rl.GRAY, font_weight=FontWeight.ROMAN, max_width=480, wrap_text=False)
    self._date_label = UnifiedLabel("", font_size=36, text_color=rl.GRAY, font_weight=FontWeight.ROMAN, max_width=480, wrap_text=False)
    self._branch_label = UnifiedLabel("", font_size=36, text_color=rl.GRAY, font_weight=FontWeight.ROMAN, scroll=True)
    self._version_commit_label = UnifiedLabel("", font_size=36, text_color=rl.GRAY, font_weight=FontWeight.ROMAN, max_width=480, wrap_text=False)

  def show_event(self):
    super().show_event()
    self._version_text = self._get_version_text()
    self._update_params()

  def _update_params(self):
    self._experimental_mode = ui_state.params.get_bool("ExperimentalMode")
    self._force_onroad = ui_state.params.get_bool("ForceOnroad")

  def _update_state(self):
    if self.is_pressed and not self._is_pressed_prev:
      self._mouse_down_t = time.monotonic()
    elif not self.is_pressed and self._is_pressed_prev:
      self._mouse_down_t = None
      self._did_long_press = False
    self._is_pressed_prev = self.is_pressed

    if self._mouse_down_t is not None:
      if time.monotonic() - self._mouse_down_t > 0.5:
        # long gating for experimental mode - only allow toggle if longitudinal control is available
        if ui_state.has_longitudinal_control:
          self._experimental_mode = not self._experimental_mode
          ui_state.params.put("ExperimentalMode", self._experimental_mode)
        self._mouse_down_t = None
        self._did_long_press = True

    if rl.get_time() - self._last_refresh > 5.0:
      # Update version text
      self._version_text = self._get_version_text()
      self._last_refresh = rl.get_time()
      self._update_params()

  def set_callbacks(self, on_settings: Callable | None = None):
    self._on_settings_click = on_settings

  def _handle_mouse_release(self, mouse_pos: MousePos):
    if not self._did_long_press:
      # Check if tap is on the force onroad icon
      if rl.check_collision_point_rec(mouse_pos, self._force_onroad_icon.rect):
        self._force_onroad = not self._force_onroad
        ui_state.params.put_bool("ForceOnroad", self._force_onroad)
      elif rl.check_collision_point_rec(mouse_pos, self._update_icon.rect) and not self._update_in_progress:
        self._update_in_progress = True
        self._update_icon.set_updating(True)
        threading.Thread(target=self._trigger_update_and_reboot, daemon=True).start()
      elif self._on_settings_click:
        self._on_settings_click()
    self._did_long_press = False

  def _trigger_update_and_reboot(self):
    """Signal updated to fetch, wait for UpdateAvailable, then reboot."""
    os.system("pkill -SIGHUP -f system.updated.updated")
    # Poll for update to complete (UpdateAvailable becomes True)
    for _ in range(600):  # up to 10 minutes
      time.sleep(1)
      if ui_state.params.get_bool("UpdateAvailable"):
        time.sleep(2)
        HARDWARE.reboot()
        return
    # Timeout - reset state
    self._update_in_progress = False
    self._update_icon.set_updating(False)

  def _get_version_text(self) -> tuple[str, str, str, str] | None:
    version = ui_state.params.get("Version")
    branch = ui_state.params.get("GitBranch")
    commit = ui_state.params.get("GitCommit")

    if not all((version, branch, commit)):
      return None

    commit_date_raw = ui_state.params.get("GitCommitDate")
    try:
      # GitCommitDate format from get_commit_date(): '%ct %ci' e.g. "'1708012345 2024-02-15 ...'"
      unix_ts = int(commit_date_raw.strip("'").split()[0])
      date_str = datetime.datetime.fromtimestamp(unix_ts).strftime("%b %d")
    except (ValueError, IndexError, TypeError, AttributeError):
      date_str = ""

    return version, branch, commit[:7], date_str

  def _render(self, _):
    # TODO: why is there extra space here to get it to be flush?
    text_pos = rl.Vector2(self.rect.x - 2 + HOME_PADDING, self.rect.y - 16)
    self._openpilot_label.set_position(text_pos.x, text_pos.y)
    self._openpilot_label.render()

    if self._version_text is not None:
      # release branch
      release_branch = self._version_text[1] in RELEASE_BRANCHES
      version_pos = rl.Rectangle(text_pos.x, text_pos.y + self._openpilot_label.font_size + 16, 100, 44)
      self._version_label.set_text(self._version_text[0])
      self._version_label.set_position(version_pos.x, version_pos.y)
      self._version_label.render()

      self._date_label.set_text(" " + self._version_text[3])
      self._date_label.set_position(version_pos.x + self._version_label.text_width + 10, version_pos.y)
      self._date_label.render()

      self._branch_label.set_max_width(gui_app.width - self._version_label.text_width - self._date_label.text_width - 32)
      self._branch_label.set_text(" " + ("release" if release_branch else self._version_text[1]))
      self._branch_label.set_position(version_pos.x + self._version_label.text_width + self._date_label.text_width + 20, version_pos.y)
      self._branch_label.render()

      if not release_branch:
        # 2nd line
        self._version_commit_label.set_text(self._version_text[2])
        self._version_commit_label.set_position(version_pos.x, version_pos.y + self._date_label.font_size + 7)
        self._version_commit_label.render()

    # ***** Center-aligned bottom section icons *****
    self._force_onroad_icon.set_active(self._force_onroad)
    self._experimental_icon.set_visible(self._experimental_mode)
    self._mic_icon.set_visible(ui_state.recording_audio)

    footer_rect = rl.Rectangle(self.rect.x + HOME_PADDING, self.rect.y + self.rect.height - 48, self.rect.width - HOME_PADDING, 48)
    self._status_bar_layout.render(footer_rect)
