from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    MAP_PATH, PLAYER_PATHS, PLAYER_BASE, BOARD_LOC,
    PLAYER_STAT_POS, PLAYER_CARD_RECTS, PLAYER_COLORS,
    WHITE, PARCHMENT, PARCHMENT_DARK, SHADOW, TURN_GLOW,
    FONT_SIZE_SM, FONT_SIZE_NORMAL, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
)
from ui.utils import load_font, draw_text_shadow, fit_text

if TYPE_CHECKING:
    from core.game_state import GameState

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]
# 多位玩家在同一格時的錯位偏移（像素）
OVERLAP_OFFSET = 10
PLAYER_STACK_OFFSETS = [(-10, -10), (12, -10), (-10, 12), (12, 12)]
TILE_HEIGHT = 45
TILE_WIDTH = 55
HOUSE_SPRITE_SIZE = 55
DEBUG_LAND_TILE_POS = False
LAND_TILE_POS = {
    1: (160, 446), 2: (220, 446), 3: (280, 446),
    6: (407, 485), 7: (467, 485), 8: (527, 485), 9: (587, 485), 10: (647, 485), 11: (707, 485),
    13: (830, 395), 14: (830, 350),
    16: (830, 260), 17: (890, 260),
    19: (1010, 260), 20: (1010, 215), 21: (1010, 170),
    22: (890, 130),
    25: (765, 173), 26: (705, 173), 
    27: (590, 120), 28: (590, 180),
    30: (587, 260), 31: (527, 260), 
    32: (463, 175), 33: (403, 175), 34: (343, 175), 35: (283, 175),
    38: (213, 85), 39: (160, 85), 40: (100, 85),
    41: (160, 170), 42: (160, 215), 43: (160, 260), 44: (160, 305), 
    46: (43, 397), 47: (43, 440),
}


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
    dx, dy = PLAYER_STACK_OFFSETS[player_idx % len(PLAYER_STACK_OFFSETS)]
    return (bx + ox + dx, by + oy + dy)


class BoardRenderer:
    """負責棋盤底圖、玩家精靈、玩家統計數字的渲染。"""

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen  = screen
        self._map     = pygame.image.load(MAP_PATH).convert()
        self._sprites = [self._load_sprite(path) for path in PLAYER_PATHS]
        self._house_sprites = self._load_house_sprites()
        self._portraits = [
            pygame.transform.smoothscale(sprite, (58, 58))
            for sprite in self._sprites
        ]
        self._font_sm = load_font(FONT_SIZE_SM)
        self._font_normal = load_font(FONT_SIZE_NORMAL)
        self._font_stat = load_font(FONT_SIZE_MD)
        self._font_name = load_font(FONT_SIZE_XL)
        self._font_money_delta = load_font(FONT_SIZE_LG)
        self._last_money: list[int] | None = None
        self._money_flashes: dict[int, tuple[int, int]] = {}

    def _load_sprite(self, path: str) -> pygame.Surface:
        sprite = pygame.image.load(path).convert_alpha()
        for y in range(sprite.get_height()):
            for x in range(sprite.get_width()):
                r, g, b, a = sprite.get_at((x, y))
                if a and r > 238 and g > 238 and b > 238:
                    sprite.set_at((x, y), (255, 255, 255, 0))
        return sprite

    def _load_house_sprites(self) -> list[list[pygame.Surface]]:
        sprites: list[list[pygame.Surface]] = []
        for player_idx in range(1, 5):
            row = []
            for level in range(1, 5):
                path = f"assets/houses/house_p{player_idx}_lv{level}.png"
                sprite = pygame.image.load(path).convert_alpha()
                row.append(
                    pygame.transform.smoothscale(
                        sprite,
                        (HOUSE_SPRITE_SIZE, HOUSE_SPRITE_SIZE),
                    )
                )
            sprites.append(row)
        return sprites

    def _draw_land_houses(self, gs: "GameState") -> None:
        for idx, land in enumerate(gs.lands[:48]):
            if land.get_mode() != 0 or land.get_ownernum() <= 0:
                continue

            owner_idx = land.get_ownernum() - 1
            if owner_idx >= len(PLAYER_COLORS):
                continue

            tile_x, tile_y = LAND_TILE_POS.get(idx, get_sprite_pos(idx, 0))
            level_idx = max(1, min(4, land.get_level())) - 1
            sprite = self._house_sprites[owner_idx][level_idx]
            left = tile_x + (TILE_WIDTH - sprite.get_width()) // 2
            top = tile_y + (TILE_HEIGHT - sprite.get_height()) // 2
            self._screen.blit(sprite, (left, top))

    def _draw_land_tile_debug(self) -> None:
        for idx, (tile_x, tile_y) in LAND_TILE_POS.items():
            rect = pygame.Rect(tile_x, tile_y, TILE_WIDTH, TILE_HEIGHT)
            center_x, center_y = rect.center
            label = self._font_sm.render(f"{idx} ({tile_x},{tile_y})", True, WHITE)
            label_rect = label.get_rect(topleft=(tile_x, tile_y - label.get_height() - 2))

            pygame.draw.rect(self._screen, (0, 0, 0), label_rect.inflate(4, 2))
            pygame.draw.rect(self._screen, TURN_GLOW, rect, 2)
            pygame.draw.line(self._screen, (255, 60, 60), (center_x - 6, center_y), (center_x + 6, center_y), 2)
            pygame.draw.line(self._screen, (255, 60, 60), (center_x, center_y - 6), (center_x, center_y + 6), 2)
            self._screen.blit(label, label_rect.topleft)

    def sync_money_state(self, gs: "GameState") -> None:
        """Update the money baseline without showing change badges."""
        self._last_money = [player.get_money() for player in gs.players]

    def queue_money_changes(self, before_money: list[int], gs: "GameState") -> None:
        """Show money badges after a delayed visual event, such as movement."""
        now = pygame.time.get_ticks()
        current_money = [player.get_money() for player in gs.players]
        for i, money in enumerate(current_money):
            delta = money - before_money[i]
            if delta:
                self._money_flashes[i] = (delta, now)
        self._last_money = current_money[:]

    def draw(
        self,
        gs: "GameState",
        animated_positions: dict[int, tuple[float, float]] | None = None,
        visual_locs: dict[int, int] | None = None,
    ) -> None:
        """每幀呼叫一次：繪製棋盤 + 精靈 + 玩家統計。"""
        # 1. 棋盤底圖
        current_money = [player.get_money() for player in gs.players]
        now = pygame.time.get_ticks()
        if self._last_money is None:
            self._last_money = current_money[:]
        else:
            for i, money in enumerate(current_money):
                delta = money - self._last_money[i]
                if delta:
                    self._money_flashes[i] = (delta, now)
            self._last_money = current_money[:]

        self._screen.blit(self._map, (0, 0))

        # 2. 玩家精靈
        self._draw_land_houses(gs)
        if DEBUG_LAND_TILE_POS:
            self._draw_land_tile_debug()

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
            flash = self._money_flashes.get(i)
            if flash is not None:
                delta, started = flash
                elapsed = now - started
                if elapsed < 2200:
                    prefix = "+" if delta > 0 else "-"
                    color_delta = (100, 245, 130) if delta > 0 else (255, 92, 76)
                    lift = int(18 * elapsed / 2200)
                    label = f"{prefix}${abs(delta):,}"
                    label_surf = self._font_money_delta.render(label, True, color_delta)
                    badge_w = label_surf.get_width() + 20
                    badge_h = label_surf.get_height() + 10
                    badge_x = max(card_rect.x + 108, card_rect.right - badge_w - 12)
                    badge_y = sy + 8 - lift
                    badge = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
                    pygame.draw.rect(self._screen, (32, 22, 12), badge, border_radius=8)
                    pygame.draw.rect(self._screen, color_delta, badge, 2, border_radius=8)
                    draw_text_shadow(
                        self._screen,
                        self._font_money_delta,
                        label,
                        (badge.x + 10, badge.y + 4),
                        color_delta,
                        SHADOW,
                        (1, 1),
                    )
                else:
                    self._money_flashes.pop(i, None)

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
