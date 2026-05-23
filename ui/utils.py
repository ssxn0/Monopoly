"""
utils.py — UI 層共用工具

提供字型載入、矩形繪製等輔助函式。
"""

import pygame
from ui.constants import FONT_CANDIDATES


# ── 字型 ───

def load_font(size: int) -> pygame.font.Font:
    """
    依優先順序尋找系統中文字型，找不到時回退到 pygame 預設字型。
    """
    for name in FONT_CANDIDATES:
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


# ── 繪圖輔助 ───

def draw_rect_alpha(surface: pygame.Surface, color: tuple,
                    rect: tuple, alpha: int = 180) -> None:
    """
    在 surface 上繪製半透明矩形覆蓋層。
    color: (R, G, B)；alpha: 0-255。
    """
    overlay = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, (rect[0], rect[1]))


def draw_button(surface: pygame.Surface, font: pygame.font.Font,
                text: str, rect: tuple, color: tuple,
                text_color: tuple = (255, 255, 255)) -> pygame.Rect:
    """
    繪製一個帶文字的按鈕，回傳 pygame.Rect（供碰撞偵測）。
    """
    btn_rect = pygame.Rect(rect)
    pygame.draw.rect(surface, color, btn_rect, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), btn_rect, 2, border_radius=6)
    label = font.render(text, True, text_color)
    lx = btn_rect.x + (btn_rect.width  - label.get_width())  // 2
    ly = btn_rect.y + (btn_rect.height - label.get_height()) // 2
    surface.blit(label, (lx, ly))
    return btn_rect


def in_rect(pos: tuple, rect: tuple) -> bool:
    """判斷滑鼠座標 pos 是否在矩形區域 (x, y, w, h) 內。"""
    x, y, w, h = rect
    return x <= pos[0] <= x + w and y <= pos[1] <= y + h
