from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    MAP_PATH, PLAYER_PATHS, PLAYER_BASE, BOARD_LOC,
    PLAYER_STAT_POS, PLAYER_CARD_RECTS, PLAYER_COLORS,
    WHITE, PARCHMENT, PARCHMENT_DARK, SHADOW, TURN_GLOW,
    FONT_SIZE_SM, FONT_SIZE_NORMAL, FONT_SIZE_MD, FONT_SIZE_XL,
)
from ui.utils import load_font, draw_text_shadow, fit_text

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
        self._sprites = [self._load_sprite(path) for path in PLAYER_PATHS]
        self._portraits = [
            pygame.transform.smoothscale(sprite, (58, 58))
            for sprite in self._sprites
        ]
        self._font_sm = load_font(FONT_SIZE_SM)
        self._font_normal = load_font(FONT_SIZE_NORMAL)
        self._font_stat = load_font(FONT_SIZE_MD)
        self._font_name = load_font(FONT_SIZE_XL)

    def _load_sprite(self, path: str) -> pygame.Surface:
        sprite = pygame.image.load(path).convert_alpha()
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                r, g, b, a = sprite.get_at((x, y))
                if a and r > 238 and g > 238 and b > 238:
                    sprite.set_at((x, y), (255, 255, 255, 0))
        return sprite

    def draw(
        self,
        gs: "GameState",
        animated_positions: dict[int, tuple[float, float]] | None = None,
        visual_locs: dict[int, int] | None = None,
    ) -> None:
        """每幀呼叫一次：繪製棋盤 + 精靈 + 玩家統計。"""
        # 1. 棋盤底圖
        self._screen.blit(self._map, (0, 0))

        # 2. 玩家精靈
        animated_positions = animated_positions or {}
        visual_locs = visual_locs or {}
        for i, player in enumerate(gs.players):
            loc = visual_locs.get(i, player.get_locate())
            px, py = animated_positions.get(i, get_sprite_pos(loc, i))
            self._screen.blit(self._sprites[i], (px, py))

        # 3. 玩家統計（金錢 / 地產數 / 道具數）
        for i, player in enumerate(gs.players):
            info  = player.get_info()
            sx, sy = PLAYER_STAT_POS[i]
            color  = PLAYER_COLORS[i]
            card_rect = pygame.Rect(PLAYER_CARD_RECTS[i])
            is_current = i == gs.current_player_idx

            if is_current:
                glow_rect = card_rect.inflate(-8, -8)
                pygame.draw.rect(self._screen, TURN_GLOW, glow_rect, 4, border_radius=8)
                pygame.draw.rect(self._screen, WHITE, glow_rect.inflate(-8, -8), 1, border_radius=8)
                badge_text = "目前"
                badge = self._font_sm.render(badge_text, True, SHADOW)
                badge_rect = pygame.Rect(
                    card_rect.right - badge.get_width() - 18,
                    card_rect.y + 14,
                    badge.get_width() + 12,
                    badge.get_height() + 6,
                )
                pygame.draw.rect(self._screen, TURN_GLOW, badge_rect, border_radius=6)
                self._screen.blit(badge, (badge_rect.x + 6, badge_rect.y + 3))

            portrait_center = (card_rect.x + 52, card_rect.y + 48)
            portrait_pos = (
                portrait_center[0] - self._portraits[i].get_width() // 2,
                portrait_center[1] - self._portraits[i].get_height() // 2,
            )
            self._screen.blit(self._portraits[i], portrait_pos)

            text_x = card_rect.x + 116
            text_w = card_rect.right - text_x - 18
            draw_text_shadow(self._screen, self._font_name, info["name"], (sx, sy), color)
            draw_text_shadow(
                self._screen,
                self._font_stat,
                f"${info['money']:,}",
                (text_x, sy + 30),
                PARCHMENT,
            )

            loc = info["locate"]
            if loc < 48:
                land_name = gs.lands[loc].get_name()
                location = f"{loc} {land_name}"
            elif loc < 53:
                location = f"{loc} 醫院"
            else:
                location = f"{loc} 監獄"

            status_lines = [
                f"地產 {info['house_count']}  道具 {info['prop_count']}",
                f"位置 {fit_text(self._font_normal, location, text_w)}",
            ]
            if info.get("stop_round", 0) > 0:
                status_lines.append(f"暫停 {info['stop_round']} 回合")
            for j, line in enumerate(status_lines):
                draw_text_shadow(
                    self._screen,
                    self._font_normal,
                    line,
                    (text_x, sy + 58 + j * 22),
                    PARCHMENT if is_current else PARCHMENT_DARK,
                    SHADOW,
                    (1, 1),
                )
