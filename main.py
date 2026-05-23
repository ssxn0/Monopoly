"""
main.py — 大富翁進入點

遊戲流程：
  1. 初始化 Pygame、載入音樂
  2. 建立 GameState（核心引擎）
  3. 呼叫 start_round() 開始第一回合
  4. 主迴圈監聽：
       骰子區域點擊 → roll_dice() → 處理 pending（buy/upgrade/shop/card）
       道具欄點擊   → show_inventory() → 使用道具
  5. 每次行動後 end_turn() + start_round() 切換下一位玩家
  6. 破產時顯示 Game Over 畫面
"""

import sys
import os

# 確保在 monopoly-python/ 目錄下執行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

import pygame

from core.game_state import GameState
from ui.constants import (
    SCREEN_W, SCREEN_H, FPS, WINDOW_TITLE,
    MUSIC_PATH, DICE_RECT, ITEM_RECT,
    WHITE, BLACK, DARK_GRAY, GRAY, PLAYER_COLORS,
    FONT_SIZE_XL, FONT_SIZE_LG,
)
from ui.utils import load_font, draw_button, in_rect, draw_rect_alpha
from ui.board_renderer import BoardRenderer
from ui.info_panel import InfoPanel
from ui.dialog import show_confirm, show_inventory
from ui.shop_screen import show_shop
from ui.card_popup import show_card

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]


# ── 遊戲結束畫面 ──

def show_game_over(screen: pygame.Surface, loser_name: str) -> None:
    """
    顯示破產畫面，等待玩家按下 Enter 或關閉視窗。
    """
    font_big = load_font(FONT_SIZE_XL)
    font_med = load_font(FONT_SIZE_LG)
    clock    = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 200)

        msg1 = font_big.render(f"{loser_name} is Loser !", True, (220, 50, 50))
        msg2 = font_med.render("按 Enter 結束遊戲", True, GRAY)
        screen.blit(msg1, (SCREEN_W // 2 - msg1.get_width() // 2, SCREEN_H // 2 - 60))
        screen.blit(msg2, (SCREEN_W // 2 - msg2.get_width() // 2, SCREEN_H // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)


# ── 骰子點擊處理（對應 Java rotate.setOnMouseClicked）──

def handle_dice_click(screen: pygame.Surface,
                      gs: GameState,
                      renderer: BoardRenderer,
                      info_panel: InfoPanel) -> bool:
    """
    處理玩家點擊骰子區域的完整流程：
      roll → pending（buy/upgrade/shop）→ end_turn → start_round
    回傳 True 代表遊戲結束（有人破產）。
    """
    # 1. 擲骰 + 移動
    ev = gs.roll_dice()
    info_panel.add_messages(ev["messages"])
    _refresh(screen, renderer, gs, info_panel)

    # 2. 破產檢查
    if ev["game_over"]:
        show_game_over(screen, ev["loser_name"])
        return True

    # 3. 處理地格事件
    pending = ev.get("pending")

    if pending == "buy":
        info = ev["pending_info"]
        yes  = show_confirm(screen,
                            f"是否購買{info['land_name']}？",
                            f"Price: ${info['price']:,}")
        ev2  = gs.confirm_buy_land(yes)
        info_panel.add_messages(ev2["messages"])

    elif pending == "upgrade":
        info = ev["pending_info"]
        yes  = show_confirm(screen,
                            f"是否升級{info['land_name']}？",
                            f"Price: ${info['price']:,}")
        ev2  = gs.confirm_upgrade_land(yes)
        info_panel.add_messages(ev2["messages"])

    elif pending == "shop":
        show_shop(screen, gs, info_panel)

    elif pending is None:
        # 機會 / 命運卡效果 → 若有複數訊息，彈出卡片視窗
        msgs = ev["messages"]
        if len(msgs) > 1:
            # 判斷卡片類型（依訊息內容猜測）
            ctype = "fate" if any(
                k in msgs[0] for k in ["天災", "龍捲", "霧", "火", "監獄", "醫院"]
            ) else "chance"
            show_card(screen, msgs[1:], card_type=ctype)

    # 4. 結束回合
    ev_end = gs.end_turn()
    info_panel.add_messages(ev_end["messages"])

    # 5. 開始下一回合
    ev_start = gs.start_round()
    info_panel.add_messages(ev_start["messages"])

    # 若下一位玩家有 skip（留在醫院/監獄）→ 仍等待玩家點擊骰子（同 Java 行為）

    _refresh(screen, renderer, gs, info_panel)
    return False


# ── 畫面更新輔助 ──

def _refresh(screen: pygame.Surface,
             renderer: BoardRenderer,
             gs: GameState,
             info_panel: InfoPanel) -> None:
    renderer.draw(gs)
    info_panel.draw()
    pygame.display.flip()


# ── 主程式 ──

def main() -> None:
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(WINDOW_TITLE)

    # 背景音樂（對應 Java MediaPlayer.setCycleCount(INDEFINITE)）
    try:
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.play(-1)
    except Exception:
        pass   # 找不到音樂檔案時靜音繼續

    # 初始化遊戲引擎與 UI 元件
    gs          = GameState()
    renderer    = BoardRenderer(screen)
    info_panel  = InfoPanel(screen)
    font_hint   = load_font(FONT_SIZE_LG)
    clock       = pygame.time.Clock()
    game_over   = False

    # 第一回合開始
    ev_start = gs.start_round()
    info_panel.add_messages(ev_start["messages"])

    # ── 主迴圈 ──
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                # 骰子區域
                if in_rect((mx, my), DICE_RECT):
                    game_over = handle_dice_click(
                        screen, gs, renderer, info_panel
                    )

                # 道具欄按鈕
                elif in_rect((mx, my), ITEM_RECT):
                    extra = show_inventory(screen, gs, info_panel)
                    # additional_points 已在 gs.use_item() 內累積，extra 僅供顯示

        # ── 每幀繪製 ───
        renderer.draw(gs)
        info_panel.draw()

        # 提示文字：顯示當前玩家名稱與操作提示
        if not game_over:
            p = gs.current_player_idx
            hint_text = (
                f"{PLAYER_NAMES[p]} 的回合　"
                f"[左側: 骰子]  [右側: 道具欄]"
            )
            hint_surf = font_hint.render(hint_text, True, PLAYER_COLORS[p])
            screen.blit(hint_surf, (SCREEN_W // 2 - hint_surf.get_width() // 2, 6))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
