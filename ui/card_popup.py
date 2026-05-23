from __future__ import annotations
import pygame
from ui.constants import (
    SCREEN_W, SCREEN_H, WHITE, DARK_GRAY, GRAY, LIGHT_GRAY,
    FONT_SIZE_XL, FONT_SIZE_MD, FONT_SIZE_NORMAL,
)
from ui.utils import load_font, draw_rect_alpha


# 卡片類型對應標題與色彩
_CARD_STYLES = {
    "chance": {"title": "機  會", "color": (70, 130, 180)},
    "fate":   {"title": "命  運", "color": (139, 69, 19)},
}


def show_card(screen: pygame.Surface,
              messages: list[str],
              card_type: str = "chance",
              auto_close_ms: int = 2000) -> None:
    """
    顯示卡片彈窗，列出 messages 中的所有文字。
    auto_close_ms：無操作時自動關閉（毫秒）。
    點擊滑鼠左鍵也可提早關閉。
    """
    style   = _CARD_STYLES.get(card_type, _CARD_STYLES["chance"])
    font_t  = load_font(FONT_SIZE_XL)
    font_n  = load_font(FONT_SIZE_MD)
    font_sm = load_font(FONT_SIZE_NORMAL)

    # 視窗尺寸（畫面正中央）
    cw = 500
    line_h = 26
    ch = 80 + len(messages) * line_h + 30
    cx = (SCREEN_W - cw) // 2
    cy = (SCREEN_H - ch) // 2

    start_ticks = pygame.time.get_ticks()
    clock = pygame.time.Clock()

    while True:
        elapsed = pygame.time.get_ticks() - start_ticks

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return

        if elapsed >= auto_close_ms:
            return

        # 進度條（剩餘時間視覺化）
        ratio = max(0.0, 1.0 - elapsed / auto_close_ms)

        # 半透明遮罩
        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 140)

        # 卡片背景
        pygame.draw.rect(screen, DARK_GRAY, (cx, cy, cw, ch), border_radius=12)
        pygame.draw.rect(screen, style["color"], (cx, cy, cw, ch), 3, border_radius=12)

        # 卡片標題列
        pygame.draw.rect(screen, style["color"], (cx, cy, cw, 46), border_radius=12)
        t_surf = font_t.render(style["title"], True, WHITE)
        screen.blit(t_surf, (cx + (cw - t_surf.get_width()) // 2, cy + 8))

        # 訊息內容
        for i, line in enumerate(messages):
            surf = font_n.render(line, True, WHITE)
            screen.blit(surf, (cx + 20, cy + 60 + i * line_h))

        # 底部進度條（倒數）
        bar_w = int((cw - 20) * ratio)
        pygame.draw.rect(screen, GRAY,          (cx + 10, cy + ch - 14, cw - 20, 8), border_radius=4)
        pygame.draw.rect(screen, style["color"], (cx + 10, cy + ch - 14, bar_w,   8), border_radius=4)

        hint = font_sm.render("點擊繼續", True, GRAY)
        screen.blit(hint, (cx + cw - hint.get_width() - 14, cy + ch - 28))

        pygame.display.flip()
        clock.tick(60)
