from __future__ import annotations
import pygame
from collections import deque
from ui.constants import (
    INFO_X, INFO_Y, INFO_W, INFO_LINE_H, INFO_MAX, INFO_WRAP,
    PARCHMENT, PARCHMENT_DARK, SHADOW, FONT_SIZE_NORMAL,
)
from ui.utils import load_font, draw_text_shadow, wrap_text

SEPARATOR = "--------------------------------------------------------------"
INFO_HISTORY_MAX = 80
INFO_VISIBLE_LINES = min(INFO_MAX, 20)


class InfoPanel:
    """右側訊息欄，維護最多 25 行文字佇列。"""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._font   = load_font(FONT_SIZE_NORMAL)
        self._lines: deque[str] = deque(maxlen=INFO_HISTORY_MAX)
        self._scroll_offset = 0

    # ── 公開 API ───
    def add_message(self, text: str) -> None:
        """
        新增一條訊息。
        分隔線直接整行加入，其餘文字依訊息欄像素寬度換行。
        """
        if text == SEPARATOR:
            self._push(text)
            return

        for line in wrap_text(self._font, text, INFO_W):
            if len(line) <= INFO_WRAP + 8:
                self._push(line)
            else:
                self._push(line[:INFO_WRAP])
                self._push(line[INFO_WRAP:])

    def add_messages(self, texts: list) -> None:
        """批次新增多條訊息。"""
        for t in texts:
            self.add_message(t)

    def draw(self) -> None:
        """將訊息佇列渲染到畫面右側。"""
        lines = list(self._lines)
        max_scroll = max(0, len(lines) - INFO_VISIBLE_LINES)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))
        start = max(0, len(lines) - INFO_VISIBLE_LINES - self._scroll_offset)
        visible = lines[start:start + INFO_VISIBLE_LINES]

        for i, line in enumerate(visible):
            if line == SEPARATOR:
                pygame.draw.line(
                    self._screen,
                    PARCHMENT_DARK,
                    (INFO_X, INFO_Y + i * INFO_LINE_H + 10),
                    (INFO_X + INFO_W, INFO_Y + i * INFO_LINE_H + 10),
                    1,
                )
                continue
            draw_text_shadow(
                self._screen,
                self._font,
                line,
                (INFO_X, INFO_Y + i * INFO_LINE_H),
                PARCHMENT,
                SHADOW,
                (1, 1),
            )

        if max_scroll > 0:
            height = INFO_VISIBLE_LINES * INFO_LINE_H
            track_x = INFO_X + INFO_W + 8
            pygame.draw.line(
                self._screen,
                PARCHMENT_DARK,
                (track_x, INFO_Y),
                (track_x, INFO_Y + height - 4),
                2,
            )
            ratio = INFO_VISIBLE_LINES / len(lines)
            thumb_h = max(28, int(height * ratio))
            scroll_ratio = 1.0 - (self._scroll_offset / max_scroll if max_scroll else 0)
            thumb_y = INFO_Y + int((height - thumb_h) * scroll_ratio)
            pygame.draw.rect(
                self._screen,
                PARCHMENT,
                (track_x - 3, thumb_y, 6, thumb_h),
                border_radius=3,
            )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEWHEEL:
            return
        mx, my = pygame.mouse.get_pos()
        in_panel = (
            INFO_X - 12 <= mx <= INFO_X + INFO_W + 24
            and INFO_Y - 8 <= my <= INFO_Y + INFO_VISIBLE_LINES * INFO_LINE_H
        )
        if not in_panel:
            return
        max_scroll = max(0, len(self._lines) - INFO_VISIBLE_LINES)
        self._scroll_offset = max(0, min(max_scroll, self._scroll_offset + event.y))

    # ── 內部 ──

    def _push(self, text: str) -> None:
        """推入一行，deque 自動維持最多 INFO_MAX 行。"""
        self._lines.append(text)
        self._scroll_offset = 0
