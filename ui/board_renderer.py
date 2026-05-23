from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    MAP_PATH, PLAYER_PATHS, PLAYER_BASE, BOARD_LOC,
    PLAYER_STAT_POS, PLAYER_STAT_SPACING, PLAYER_COLORS,
    WHITE, FONT_SIZE_MD, FONT_SIZE_XL,
)
from ui.utils import load_font

if TYPE_CHECKING:
    from core.game_state import GameState

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]
# 多位玩家在同一格時的錯位偏移（像素）
OVERLAP_OFFSET = 10


def get_sprite_pos(locate: int, player_idx: int) -> tuple[int, int]:
    """
    把玩家邏輯位置 locate 轉換成螢幕座標。
    player_idx 0-3 各自錯開 OVERLAP_OFFSET px 避免重疊。
    """
    bx, by = PLAYER_BASE
    if locate < len(BOARD_LOC):
        ox, oy = BOARD_LOC[locate]
    else:
        ox, oy = 0, 0
    offset = player_idx * OVERLAP_OFFSET
    return (bx + ox + offset, by + oy + offset)


class BoardRenderer:
    """負責棋盤底圖、玩家精靈、玩家統計數字的渲染。"""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen  = screen
        self._map     = pygame.image.load(MAP_PATH).convert()
        self._sprites = [
            pygame.image.load(path).convert_alpha()
            for path in PLAYER_PATHS
        ]
        self._font_stat = load_font(FONT_SIZE_MD)
        self._font_name = load_font(FONT_SIZE_XL)

    def draw(self, gs: "GameState") -> None:
        """每幀呼叫一次：繪製棋盤 + 精靈 + 玩家統計。"""
        # 1. 棋盤底圖
        self._screen.blit(self._map, (0, 0))

        # 2. 玩家精靈
        for i, player in enumerate(gs.players):
            loc = player.get_locate()
            px, py = get_sprite_pos(loc, i)
            self._screen.blit(self._sprites[i], (px, py))

        # 3. 玩家統計（金錢 / 地產數 / 道具數）
        for i, player in enumerate(gs.players):
            info  = player.get_info()
            sx, sy = PLAYER_STAT_POS[i]
            color  = PLAYER_COLORS[i]

            # 玩家名稱（識別色）
            name_surf = self._font_name.render(info["name"], True, color)
            self._screen.blit(name_surf, (sx, sy - PLAYER_STAT_SPACING))

            # 三行資訊（白色）
            lines = [
                f"${info['money']:,}",
                f"房: {info['house_count']}",
                f"具: {info['prop_count']}",
            ]
            for j, line in enumerate(lines):
                surf = self._font_stat.render(line, True, WHITE)
                self._screen.blit(surf, (sx, sy + j * PLAYER_STAT_SPACING))
