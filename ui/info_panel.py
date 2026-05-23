from __future__ import annotations
import pygame
from collections import deque
from ui.constants import (
    INFO_X, INFO_Y, INFO_LINE_H, INFO_MAX, INFO_WRAP,
    WHITE, FONT_SIZE_NORMAL,
)
from ui.utils import load_font

SEPARATOR = "--------------------------------------------------------------"


class InfoPanel:
    """右側訊息欄，維護最多 25 行文字佇列。"""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._font   = load_font(FONT_SIZE_NORMAL)
        self._lines: deque[str] = deque(maxlen=INFO_MAX)

    # ── 公開 API ───
    def add_message(self, text: str) -> None:
        """
        新增一條訊息。
        對應 Java Information.setText()：
          - 分隔線直接整行加入
          - 超過 INFO_WRAP 字元則切成兩行
        """
        if text == SEPARATOR or len(text) <= INFO_WRAP:
            self._push(text)
        else:
            self._push(text[:INFO_WRAP])
            self._push(text[INFO_WRAP:])

    def add_messages(self, texts: list) -> None:
        """批次新增多條訊息。"""
        for t in texts:
            self.add_message(t)

    def draw(self) -> None:
        """將訊息佇列渲染到畫面右側。"""
        for i, line in enumerate(self._lines):
            surf = self._font.render(line, True, WHITE)
            self._screen.blit(surf, (INFO_X, INFO_Y + i * INFO_LINE_H))

    # ── 內部 ──

    def _push(self, text: str) -> None:
        """推入一行，deque 自動維持最多 INFO_MAX 行。"""
        self._lines.append(text)
