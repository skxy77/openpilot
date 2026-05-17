"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl
from openpilot.system.hardware import HARDWARE
from openpilot.system.ui.widgets.nav_widget import NavWidget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.lib.application import gui_app, FontWeight


BUTTON_WIDTH = 400
BUTTON_HEIGHT = 120
BUTTON_SPACING = 30
BUTTON_RADIUS = 0.35


class UpdateConfirmationDialog(NavWidget):
  """Dialog shown when tapping the update alert on mici (comma 4).
  Provides 'Reboot and Update' and 'Later' buttons."""

  def __init__(self, version_string: str = ""):
    super().__init__()
    self.set_rect(rl.Rectangle(0, 0, gui_app.width, gui_app.height))

    title = "Update Ready"
    if version_string:
      title += f"\n{version_string}"

    self._title_label = UnifiedLabel(title, font_size=64, font_weight=FontWeight.BOLD,
                                     text_color=rl.WHITE,
                                     alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                     alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

    self._reboot_label = UnifiedLabel("Reboot and Update", font_size=48, font_weight=FontWeight.MEDIUM,
                                      text_color=rl.BLACK,
                                      alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                      alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

    self._later_label = UnifiedLabel("Later", font_size=48, font_weight=FontWeight.MEDIUM,
                                     text_color=rl.WHITE,
                                     alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                     alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

    self._reboot_rect = rl.Rectangle(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)
    self._later_rect = rl.Rectangle(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT)

    self._reboot_pressed = False
    self._later_pressed = False

  def _update_state(self):
    super()._update_state()
    last_mouse = gui_app.last_mouse_event

    self._reboot_pressed = last_mouse.left_down and rl.check_collision_point_rec(last_mouse.pos, self._reboot_rect)
    self._later_pressed = last_mouse.left_down and rl.check_collision_point_rec(last_mouse.pos, self._later_rect)

    if last_mouse.left_released:
      if rl.check_collision_point_rec(last_mouse.pos, self._reboot_rect):
        HARDWARE.reboot()
      elif rl.check_collision_point_rec(last_mouse.pos, self._later_rect):
        self.dismiss()

  def _render(self, _):
    # Background
    rl.draw_rectangle_rec(self._rect, rl.Color(30, 30, 30, 255))

    center_x = self._rect.x + self._rect.width / 2
    center_y = self._rect.y + self._rect.height / 2

    # Title
    title_rect = rl.Rectangle(center_x - 300, center_y - 200, 600, 120)
    self._title_label.render(title_rect)

    # Reboot and Update button (white)
    self._reboot_rect = rl.Rectangle(center_x - BUTTON_WIDTH / 2, center_y - 20, BUTTON_WIDTH, BUTTON_HEIGHT)
    reboot_color = rl.Color(200, 200, 200, 255) if self._reboot_pressed else rl.WHITE
    rl.draw_rectangle_rounded(self._reboot_rect, BUTTON_RADIUS, 10, reboot_color)
    self._reboot_label.render(self._reboot_rect)

    # Later button (dark/outline)
    self._later_rect = rl.Rectangle(center_x - BUTTON_WIDTH / 2, center_y - 20 + BUTTON_HEIGHT + BUTTON_SPACING,
                                    BUTTON_WIDTH, BUTTON_HEIGHT)
    later_color = rl.Color(100, 100, 100, 255) if self._later_pressed else rl.Color(79, 79, 79, 255)
    rl.draw_rectangle_rounded(self._later_rect, BUTTON_RADIUS, 10, later_color)
    self._later_label.render(self._later_rect)
