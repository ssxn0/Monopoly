from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    SCREEN_W, SCREEN_H, WHITE,
    BTN_NORMAL, BTN_YES, PLAYER_COLORS,
    PARCHMENT, PARCHMENT_DARK, TURN_GLOW,
    FONT_SIZE_XL, FONT_SIZE_LG, FONT_SIZE_MD, FONT_SIZE_NORMAL,
)
from ui.utils import (
    load_font, draw_rect_alpha, draw_rounded_rect_alpha,
    draw_button, in_rect, fit_text,
)

if TYPE_CHECKING:
    from core.game_state import GameState
    from ui.info_panel import InfoPanel


SHOP_TITLE = "\u5546\u5e97"
MONEY_LABEL = "\u73fe\u6709\u91d1\u9322\uff1a"
BUY_LABEL = "\u8cfc\u8cb7"
PURCHASED_LABEL = "\u5df2\u8cfc\u8cb7"
LOCKED_LABEL = "\u5df2\u9396\u5b9a"
CLOSE_LABEL = "\u96e2\u958b\u5546\u5e97"
BOUGHT_NOTICE = (
    "\u672c\u6b21\u9032\u5e97\u5df2\u8cfc\u8cb7 1 "
    "\u4ef6\u9053\u5177\uff0c\u8acb\u96e2\u958b\u5546\u5e97\u3002"
)


def show_shop(screen: pygame.Surface,
              gs: "GameState",
              info_panel: "InfoPanel",
              draw_background=None) -> dict:
    font_t = load_font(FONT_SIZE_XL)
    font_n = load_font(FONT_SIZE_LG)
    font_sm = load_font(FONT_SIZE_MD)
    font_xs = load_font(FONT_SIZE_NORMAL)

    p = gs.current_player_idx
    player = gs.players[p]
    items = gs.get_shop_display()

    sw, sh = 620, 520
    sx = (SCREEN_W - sw) // 2
    sy = (SCREEN_H - sh) // 2

    row_h = 66
    list_y = sy + 116
    text_x = sx + 28
    buy_w, buy_h = 106, 38
    buy_x = sx + sw - buy_w - 30
    text_w = buy_x - text_x - 22
    close_rect = (sx + sw // 2 - 100, sy + sh - 52, 200, 40)
    purchased_item: int | None = None
    purchased_name = ""

    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if in_rect((mx, my), close_rect):
                    ev = gs.close_shop()
                    info_panel.add_messages(ev["messages"])
                    return ev

                if purchased_item is not None:
                    continue

                for i, item in enumerate(items):
                    row_y = list_y + i * row_h
                    buy_rect = (buy_x, row_y + 14, buy_w, buy_h)
                    if not in_rect((mx, my), buy_rect):
                        continue
                    if player.get_money() < item["price"]:
                        continue

                    ev = gs.buy_shop_item(item["idx"])
                    info_panel.add_messages(ev["messages"])
                    if ev["game_over"]:
                        return ev
                    if ev.get("updated_players"):
                        purchased_item = item["idx"]
                        purchased_name = item["name"]
                    break

        if draw_background is not None:
            draw_background()
        draw_rect_alpha(screen, (20, 14, 6), (0, 0, SCREEN_W, SCREEN_H), 90)

        draw_rounded_rect_alpha(screen, PARCHMENT, (sx + 8, sy + 10, sw, sh), 70, border_radius=16)
        draw_rounded_rect_alpha(screen, (52, 38, 20), (sx, sy, sw, sh), 232, border_radius=16)
        pygame.draw.rect(screen, PLAYER_COLORS[p], (sx, sy, sw, sh), 3, border_radius=16)
        pygame.draw.rect(screen, TURN_GLOW, (sx + 10, sy + 10, sw - 20, sh - 20), 1, border_radius=12)

        title = font_t.render(SHOP_TITLE, True, PLAYER_COLORS[p])
        screen.blit(title, (sx + (sw - title.get_width()) // 2, sy + 18))

        money_surf = font_sm.render(f"{MONEY_LABEL}${player.get_money():,}", True, PARCHMENT)
        screen.blit(money_surf, (sx + 28, sy + 58))
        if purchased_item is not None:
            notice_text = f"{BOUGHT_NOTICE}  + {purchased_name}"
            notice = font_xs.render(fit_text(font_xs, notice_text, sw - 56), True, TURN_GLOW)
            screen.blit(notice, (sx + 28, sy + 86))

        for i, item in enumerate(items):
            row_y = list_y + i * row_h
            if item["idx"] == purchased_item:
                draw_rounded_rect_alpha(
                    screen,
                    PLAYER_COLORS[p],
                    (sx + 18, row_y - 2, sw - 36, row_h - 4),
                    70,
                    border_radius=8,
                )
                pygame.draw.rect(
                    screen,
                    TURN_GLOW,
                    (sx + 18, row_y - 2, sw - 36, row_h - 4),
                    2,
                    border_radius=8,
                )
            pygame.draw.line(
                screen,
                PARCHMENT_DARK,
                (sx + 14, row_y - 4),
                (sx + sw - 14, row_y - 4),
            )

            name = f"{item['name']}   ${item['price']:,}"
            name_surf = font_sm.render(fit_text(font_sm, name, text_w), True, WHITE)
            screen.blit(name_surf, (text_x, row_y + 6))

            desc = item["info"].split("\n")[-1]
            desc_surf = font_xs.render(fit_text(font_xs, desc, text_w), True, PARCHMENT)
            screen.blit(desc_surf, (text_x, row_y + 32))

            buy_rect = (buy_x, row_y + 14, buy_w, buy_h)
            can_buy = player.get_money() >= item["price"] and purchased_item is None
            if can_buy and in_rect((mx, my), buy_rect):
                color = BTN_YES
            elif can_buy:
                color = BTN_NORMAL
            else:
                color = (80, 80, 80)

            if item["idx"] == purchased_item:
                label = PURCHASED_LABEL
            elif purchased_item is not None:
                label = LOCKED_LABEL
            else:
                label = BUY_LABEL
            draw_button(screen, font_sm, label, buy_rect, color)

        cc = (80, 80, 80) if not in_rect((mx, my), close_rect) else (110, 110, 110)
        draw_button(screen, font_n, CLOSE_LABEL, close_rect, cc)

        pygame.display.flip()
        clock.tick(60)
