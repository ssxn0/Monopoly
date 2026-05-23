from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    SCREEN_W, SCREEN_H, WHITE, DARK_GRAY, GRAY, LIGHT_GRAY,
    BTN_NORMAL, BTN_YES, PLAYER_COLORS,
    FONT_SIZE_XL, FONT_SIZE_LG, FONT_SIZE_MD, FONT_SIZE_NORMAL,
)
from ui.utils import load_font, draw_rect_alpha, draw_button, in_rect

if TYPE_CHECKING:
    from core.game_state import GameState
    from ui.info_panel import InfoPanel


def show_shop(screen: pygame.Surface,
              gs: "GameState",
              info_panel: "InfoPanel") -> dict:
    """
    顯示商店視窗，玩家可購買多件道具，點擊「離開商店」關閉。
    """
    font_t  = load_font(FONT_SIZE_XL)
    font_n  = load_font(FONT_SIZE_LG)
    font_sm = load_font(FONT_SIZE_MD)
    font_xs = load_font(FONT_SIZE_NORMAL)

    p      = gs.current_player_idx
    player = gs.players[p]
    items  = gs.get_shop_display()

    # 視窗尺寸（畫面正中央）
    sw, sh = 500, 420
    sx = (SCREEN_W - sw) // 2
    sy = (SCREEN_H - sh) // 2

    close_rect = (sx + sw // 2 - 90, sy + sh - 60, 180, 40)

    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 關閉按鈕
                if in_rect((mx, my), close_rect):
                    ev = gs.close_shop()
                    info_panel.add_messages(ev["messages"])
                    return ev
                # 各道具購買按鈕
                for i, item in enumerate(items):
                    buy_rect = (sx + sw - 120, sy + 90 + i * 60, 90, 34)
                    if in_rect((mx, my), buy_rect):
                        ev = gs.buy_shop_item(item["idx"])
                        info_panel.add_messages(ev["messages"])
                        if ev["game_over"]:
                            return ev

        # 半透明遮罩
        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 160)

        # 視窗背景
        pygame.draw.rect(screen, DARK_GRAY, (sx, sy, sw, sh), border_radius=12)
        pygame.draw.rect(screen, GRAY,      (sx, sy, sw, sh), 2, border_radius=12)

        # 標題
        title = font_t.render("商店", True, PLAYER_COLORS[p])
        screen.blit(title, (sx + (sw - title.get_width()) // 2, sy + 18))

        # 玩家金錢
        money_surf = font_sm.render(f"現有金錢：${player.get_money():,}", True, LIGHT_GRAY)
        screen.blit(money_surf, (sx + 20, sy + 55))

        # 道具列表
        for i, item in enumerate(items):
            row_y = sy + 90 + i * 60

            # 分隔線
            pygame.draw.line(screen, GRAY, (sx + 10, row_y - 4), (sx + sw - 10, row_y - 4))

            # 名稱 + 價格
            name_surf = font_sm.render(
                f"{item['name']}　${item['price']:,}", True, WHITE)
            screen.blit(name_surf, (sx + 18, row_y + 4))

            # 說明（取第一行）
            desc = item["info"].split("\n")[-1]
            desc_surf = font_xs.render(desc, True, LIGHT_GRAY)
            screen.blit(desc_surf, (sx + 18, row_y + 26))

            # 購買按鈕
            buy_rect = (sx + sw - 120, row_y + 10, 90, 34)
            can_buy  = player.get_money() >= item["price"]
            bc = BTN_NORMAL if (can_buy and not in_rect((mx, my), buy_rect)) \
                 else BTN_YES if (can_buy and in_rect((mx, my), buy_rect)) \
                 else (80, 80, 80)
            draw_button(screen, font_sm, "購買", buy_rect, bc)

        # 關閉按鈕
        cc = (80, 80, 80) if not in_rect((mx, my), close_rect) else (110, 110, 110)
        draw_button(screen, font_n, "離開商店", close_rect, cc)

        pygame.display.flip()
        clock.tick(60)
