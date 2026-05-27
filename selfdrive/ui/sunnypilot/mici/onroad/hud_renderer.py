"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl

from cereal import log
from openpilot.selfdrive.ui.mici.onroad.hud_renderer import HudRenderer, COLORS
from openpilot.selfdrive.ui.sunnypilot.onroad.blind_spot_indicators import BlindSpotIndicators
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached

LEAD_DIST_FONT_SIZE = 50
PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants


class HudRendererSP(HudRenderer):
  def __init__(self):
    super().__init__()
    self.blind_spot_indicators = BlindSpotIndicators()
    self.lead_dist: float = 0.0
    self.lead_status: bool = False
    self._font_bold_sp: rl.Font = gui_app.font(FontWeight.BOLD)

  def _update_state(self) -> None:
    super()._update_state()
    self.blind_spot_indicators.update()

    if ui_state.started and ui_state.sm.recv_frame.get('selfdriveState', 0) > 0:
      ui_state.personality = PERSONALITY_TO_INT[ui_state.sm['selfdriveState'].personality]
    else:
      ui_state.personality = ui_state.params.get("LongitudinalPersonality", return_default=True)

    if ui_state.sm.recv_frame.get('radarState', 0) > 0:
      lead_one = ui_state.sm['radarState'].leadOne
      self.lead_status = lead_one.status
      self.lead_dist = lead_one.dRel
    else:
      self.lead_status = False
      self.lead_dist = 0.0

  def _draw_lead_distance(self, rect: rl.Rectangle) -> None:
    if not self.lead_status:
      dist_text = "-- m" if ui_state.is_metric else "-- ft"
      color = COLORS.WHITE
    else:
      dist = self.lead_dist
      if ui_state.is_metric:
        dist_text = f"{dist:.1f}m"
      else:
        dist_text = f"{dist * 3.28084:.0f}ft"

      if dist < 10:
        color = rl.RED
      elif dist < 25:
        color = rl.Color(255, 188, 0, 255)
      else:
        color = COLORS.WHITE

    box_w = 180
    box_h = 60
    box_x = rect.x + rect.width - box_w - 10
    box_y = rect.y + 10

    bg_rect = rl.Rectangle(box_x, box_y, box_w, box_h)
    rl.draw_rectangle_rounded(bg_rect, 0.3, 10, rl.Color(0, 0, 0, 166))

    text_size = measure_text_cached(self._font_bold_sp, dist_text, LEAD_DIST_FONT_SIZE)
    text_x = box_x + (box_w - text_size.x) / 2
    text_y = box_y + (box_h - text_size.y) / 2
    rl.draw_text_ex(self._font_bold_sp, dist_text, rl.Vector2(text_x, text_y), LEAD_DIST_FONT_SIZE, 0, color)

  def _draw_driving_mode_bars(self, rect: rl.Rectangle) -> None:
    """Draw bars indicating driving mode: 1=traffic, 2=aggressive, 3=standard, 4=relaxed."""
    num_bars = ui_state.personality + 1
    max_bars = 4

    bar_w = 30
    bar_h = 8
    gap = 5
    total_h = max_bars * bar_h + (max_bars - 1) * gap
    # Align right edge with the lead distance box (180px wide, 10px from right)
    lead_box_right = rect.x + rect.width - 10
    box_x = lead_box_right - bar_w
    # Position below lead distance box (box_y=10, box_h=60, plus spacing)
    box_y = rect.y + 10 + 60 + 10

    bg_rect = rl.Rectangle(box_x, box_y, bar_w, total_h + 10)
    rl.draw_rectangle_rounded(bg_rect, 0.3, 10, rl.Color(0, 0, 0, 166))

    for i in range(max_bars):
      bar_x = box_x + 5
      bar_y = box_y + 5 + i * (bar_h + gap)
      if i < num_bars:
        bar_color = rl.Color(255, 255, 255, 220)
      else:
        bar_color = rl.Color(255, 255, 255, 50)
      rl.draw_rectangle_rounded(rl.Rectangle(bar_x, bar_y, bar_w - 10, bar_h), 0.5, 6, bar_color)

  def _render(self, rect: rl.Rectangle) -> None:
    super()._render(rect)
    self.blind_spot_indicators.render(rect)
    self._draw_lead_distance(rect)
    self._draw_driving_mode_bars(rect)

  def _has_blind_spot_detected(self) -> bool:

    return self.blind_spot_indicators.detected
