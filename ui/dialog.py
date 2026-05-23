from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

from ui.constants import (
    SCREEN_W, SCREEN_H, WHITE, BLACK, DARK_GRAY, GRAY, LIGHT_GRAY,
    BTN_YES, BTN_NO, BTN_NORMAL, PLAYER_COLORS,
    FONT_SIZE_LG, FONT_SIZE_MD, FONT_SIZE_NORMAL,
)
from ui.utils import load_font, draw_rect_alpha, draw_button, in_rect

if TYPE_CHECKING:
    from core.game_state import GameState
    from ui.info_panel import InfoPanel

# ── 確認對話框（購買 / 升級）──

def show_confirm(screen: pygame.Surface,
                 header: str, content: str) -> bool:
    """
    顯示「是 / 否」確認對話框，阻塞直到玩家選擇。
    對應 Java NewStage.Action() / Action2()。

    回傳 True（是）或 False（否）。
    """
    font_h  = load_font(FONT_SIZE_LG)
    font_c  = load_font(FONT_SIZE_MD)

    # 對話框尺寸與位置（畫面正中央）
    dw, dh = 420, 200
    dx = (SCREEN_W - dw) // 2
    dy = (SCREEN_H - dh) // 2

    yes_rect = (dx + 60,  dy + 130, 120, 44)
    no_rect  = (dx + 240, dy + 130, 120, 44)

    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if in_rect((mx, my), yes_rect):
                    return True
                if in_rect((mx, my), no_rect):
                    return False

        # 半透明遮罩
        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 160)

        # 對話框背景
        pygame.draw.rect(screen, DARK_GRAY, (dx, dy, dw, dh), border_radius=10)
        pygame.draw.rect(screen, GRAY,      (dx, dy, dw, dh), 2, border_radius=10)

        # 標題
        h_surf = font_h.render(header, True, WHITE)
        screen.blit(h_surf, (dx + (dw - h_surf.get_width()) // 2, dy + 30))

        # 內文
        c_surf = font_c.render(content, True, LIGHT_GRAY)
        screen.blit(c_surf, (dx + (dw - c_surf.get_width()) // 2, dy + 80))

        # 按鈕
        y_color = BTN_YES if not in_rect((mx, my), yes_rect) else (80, 180, 120)
        n_color = BTN_NO  if not in_rect((mx, my), no_rect)  else (220, 80, 80)
        draw_button(screen, font_c, "是", yes_rect, y_color)
        draw_button(screen, font_c, "否", no_rect,  n_color)

        pygame.display.flip()
        clock.tick(60)


# ── 道具欄視窗（對應 Java Main.PlaywithProp()）──

def show_inventory(screen: pygame.Surface,
                   gs: "GameState",
                   info_panel: "InfoPanel") -> int:
    """
    顯示當前玩家的道具欄視窗，阻塞直到玩家關閉。
    若玩家使用了骰子道具，回傳額外步數（>0）；否則回傳 0。
    """
    from ui.info_panel import InfoPanel  # 避免循環 import

    font_t  = load_font(FONT_SIZE_LG)
    font_n  = load_font(FONT_SIZE_MD)
    font_sm = load_font(FONT_SIZE_NORMAL)

    p    = gs.current_player_idx
    name = gs.players[p].name

    extra_points = 0

    # 視窗尺寸與位置
    pw, ph = 460, 360
    px_box = (SCREEN_W - pw) // 2
    py_box = (SCREEN_H - ph) // 2

    close_rect = (px_box + pw - 110, py_box + ph - 60, 90, 36)

    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()
        prop   = gs.players[p].get_prop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if in_rect((mx, my), close_rect):
                    return extra_points
                # 道具按鈕
                for slot, item_idx in enumerate(prop):
                    use_rect = (px_box + pw - 110, py_box + 80 + slot * 52, 80, 32)
                    if in_rect((mx, my), use_rect) and item_idx == 0:
                        ev = gs.use_item(slot)
                        info_panel.add_messages(ev["messages"])
                        extra_points += gs.additional_points
                        break

        # 背景遮罩
        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 160)

        # 視窗
        pygame.draw.rect(screen, DARK_GRAY, (px_box, py_box, pw, ph), border_radius=10)
        pygame.draw.rect(screen, GRAY,      (px_box, py_box, pw, ph), 2, border_radius=10)

        # 標題
        title = font_t.render(f"{name} 的道具欄", True, PLAYER_COLORS[p])
        screen.blit(title, (px_box + (pw - title.get_width()) // 2, py_box + 20))

        if not prop:
            msg = font_n.render("目前沒有任何道具", True, GRAY)
            screen.blit(msg, (px_box + (pw - msg.get_width()) // 2, py_box + 130))
        else:
            for slot, item_idx in enumerate(prop):
                item = gs._shop.get_prop(item_idx)
                row_y = py_box + 80 + slot * 52

                # 道具名稱
                item_surf = font_n.render(f"{slot+1}. {item.get_name()}", True, WHITE)
                screen.blit(item_surf, (px_box + 20, row_y + 8))

                # 說明（第一行）
                info_line = item.get_information().split("\n")[0]
                info_surf = font_sm.render(info_line, True, LIGHT_GRAY)
                screen.blit(info_surf, (px_box + 20, row_y + 28))

                # 使用按鈕（只有骰子可主動使用）
                if item_idx == 0:
                    use_rect = (px_box + pw - 110, row_y + 10, 80, 32)
                    uc = BTN_NORMAL if not in_rect((mx, my), use_rect) else BTN_YES
                    draw_button(screen, font_sm, "使用", use_rect, uc)

        # 關閉按鈕
        cc = (100, 100, 100) if not in_rect((mx, my), close_rect) else (140, 140, 140)
        draw_button(screen, font_n, "關閉", close_rect, cc)

        pygame.display.flip()
        clock.tick(60)
