from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional

from core.dice import Dice
from core.land import Land
from core.player import Player
from core.chance_card import ChanceCard
from core.fate_card import FateCard
from core.shop import Shop

# ── 常數 ──────────────────────────────────────────────────────────────────────

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]
BOARD_SIZE = 48
_BOARD_JSON = Path(__file__).parent.parent / "data" / "board.json"

# ── 硬編碼備援資料 ──────────────────────────────────────────────────────────

_FALLBACK_PRICES = [
    0, 5000, 5000, 5000, 0, 0, 6000, 6000, 6000, 6500, 6500, 6500,
    0, 15000, 0, 0, 7000, 7000, 0, 7500, 8000, 9000, 9000, 0, 0,
    9500, 9500, 15000, 0, 0, 10000, 10000, 11000, 11000, 11000, 11000,
    0, 0, 11500, 11500, 11500, 12000, 12000, 12000, 12000, 0, 12500, 12500,
]
_FALLBACK_NAMES = [
    "起點", "森林入口I", "森林入口II", "森林入口III", "什麼都沒有的地方",
    "命運", "狡兔I窟", "狡兔II窟", "狡兔III窟", "熊二的家", "老鼠洞", "草叢",
    "機會", "水濂洞", "水濂洞", "瀑布下游", "蜂窩", "螞蟻窩", "商店",
    "豬大哥家", "豬二哥家", "豬小弟家", "漂漂屋", "命運", "什麼都沒有的地方",
    "浪浪之家I", "浪浪之家II", "花果山", "花果山", "瀑布上游",
    "蚯蚓在泥土裡的家", "鳥巢", "雷文克勞", "史萊哲林", "赫夫帕夫", "葛萊芬多",
    "機會", "什麼都沒有的地方", "巨人的家I", "巨人的家II", "獨角獸的領地",
    "破舊露營車", "狼群領域", "美女與野獸的家", "廢棄工地", "商店",
    "廢棄豪宅", "怪獸與牠們的產地",
]
_FALLBACK_MODES = [
    -1, 0, 0, 0, -1, 2, 0, 0, 0, 0, 0, 0,
    1, 0, 0, -1, 0, 0, 3, 0, 0, 0, 0, 2, -1,
    0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0,
    1, -1, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0,
]
# 共用同一 Land 物件的索引對
_SHARED_LANDS = {14: 13, 28: 27}


# ── 輔助函式 ──────────────────────────────────────────────────────────────────

def _make_event(
    messages: Optional[List[str]] = None,
    pending: Optional[str] = None,
    pending_info: Optional[dict] = None,
    game_over: bool = False,
    loser_name: Optional[str] = None,
    updated_players: Optional[List[int]] = None,
) -> dict:
    return {
        "messages": messages or [],
        "pending": pending,
        "pending_info": pending_info or {},
        "game_over": game_over,
        "loser_name": loser_name,
        "updated_players": list(set(updated_players or [])),
    }


# ── 核心遊戲狀態 ──────────────────────────────────────────────────────────────

class GameState:
    """
    大富翁遊戲核心狀態機。

    使用方式（UI 層呼叫順序）：
        gs = GameState()
        ev = gs.start_round()          # 回合開始，顯示當前玩家
        ev = gs.roll_dice()            # 玩家點擊骰子區域
        if ev["pending"] == "buy":
            ev = gs.confirm_buy_land(True/False)
        elif ev["pending"] == "upgrade":
            ev = gs.confirm_upgrade_land(True/False)
        elif ev["pending"] == "shop":
            # UI 顯示商店 → 玩家選擇購買
            gs.buy_shop_item(item_idx)  # 可呼叫多次
            ev = gs.close_shop()
        ev = gs.end_turn()             # 結束本回合，切換到下一位玩家
    """

    def __init__(self) -> None:
        # 初始化棋盤
        self.lands: List[Land] = self._init_board()

        # 初始化四位玩家
        self.players: List[Player] = [Player(i + 1) for i in range(4)]

        # 回合計數與當前玩家
        self.round: int = 0
        self.current_player_idx: int = 0   # 0–3

        # 額外步數（道具使用後累積）
        self.additional_points: int = 0

        # 各系統
        self._dice = Dice()
        self._chance = ChanceCard()
        self._fate = FateCard()
        self._shop = Shop()

        # 待確認狀態
        self._pending: Optional[str] = None
        self._pending_land_idx: Optional[int] = None

    def _bankruptcy_event(self, updated_players: Optional[List[int]] = None) -> dict:
        updated = list(updated_players or [])
        for idx, player in enumerate(self.players):
            if player.is_bankrupt():
                if idx not in updated:
                    updated.append(idx)
                return {
                    "game_over": True,
                    "loser_name": PLAYER_NAMES[idx],
                    "message": f"{PLAYER_NAMES[idx]} is Loser !",
                    "updated_players": updated,
                }
        return {
            "game_over": False,
            "loser_name": None,
            "message": None,
            "updated_players": updated,
        }

    # ── 棋盤初始化 ────────────────────────────────────────────────────────────

    def _init_board(self) -> List[Land]:
        """從 board.json 建立 48 格地產，若讀取失敗則使用硬編碼備援。"""
        lands: List[Optional[Land]] = [None] * BOARD_SIZE
        try:
            data = json.loads(_BOARD_JSON.read_text(encoding="utf-8"))
            for entry in data:
                idx = entry["idx"]
                if "shared_with" in entry:
                    # 延後處理，先建立自己的物件
                    lands[idx] = Land(entry["name"], entry["price"], entry["mode"])
                else:
                    lands[idx] = Land(entry["name"], entry["price"], entry["mode"])
            # 套用共用 Land（land[14]=land[13], land[28]=land[27]）
            for child, parent in _SHARED_LANDS.items():
                lands[child] = lands[parent]
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            for i in range(BOARD_SIZE):
                lands[i] = Land(_FALLBACK_NAMES[i], _FALLBACK_PRICES[i], _FALLBACK_MODES[i])
            for child, parent in _SHARED_LANDS.items():
                lands[child] = lands[parent]
        return lands  # type: ignore[return-value]

    # ── 公開 API ──────────────────────────────────────────────────────────────

    def start_round(self) -> dict:
        """
        回合開始：顯示當前玩家名稱與狀態。
        若玩家在醫院 / 監獄且 stop_round > 0 → 自動跳過此回合（扣除 1 輪）。
        回傳事件字典，UI 層據此顯示「請擲骰子」或「跳過回合」提示。
        """
        p = self.current_player_idx
        player = self.players[p]
        name = PLAYER_NAMES[p]

        messages = [f"{name} 的回合（請執行操作）:"]

        skip = False
        if player.is_in_hospital() and player.stop_round > 0:
            player.stop_round -= 1
            messages.append(f"{name} 在醫院休養，跳過本回合（剩餘 {player.stop_round} 輪）")
            skip = True
        elif player.is_in_jail() and player.stop_round > 0:
            player.stop_round -= 1
            messages.append(f"{name} 在監獄服刑，跳過本回合（剩餘 {player.stop_round} 輪）")
            skip = True

        return _make_event(
            messages=messages,
            pending="skip" if skip else None,
            updated_players=[p],
        )

    def roll_dice(self) -> dict:
        """
        玩家擲骰子：移動後觸發對應地格事件。
        呼叫前可先呼叫 use_item() 累積 additional_points。

        回傳事件字典，pending 可能為：
          None     → 自動處理完畢，UI 可直接呼叫 end_turn()
          "buy"    → 需向玩家確認購買，UI 顯示確認對話框
          "upgrade"→ 需向玩家確認升級，UI 顯示確認對話框
          "shop"   → 玩家到達商店，UI 顯示商店視窗
        """
        p = self.current_player_idx
        player = self.players[p]
        name = PLAYER_NAMES[p]

        # 擲骰
        points = self._dice.rotate() + self.additional_points
        loc = player.move(points)

        messages = [f"{name} 骰到 {points}, 到了{self.lands[loc].name}"]
        updated = [p]
        pending = None
        pending_info: dict = {}

        # 只在主棋盤（0–47）上觸發地格事件
        if player.is_on_board():
            land = self.lands[loc]
            mode = land.get_mode()

            if mode == 0:
                result = self._normal_action(p, loc)
                messages += result["messages"]
                updated += result.get("updated_players", [])
                pending = result.get("pending")
                pending_info = result.get("pending_info", {})

            elif mode == 1:   # 機會卡
                result = self._chance.operate(self.players, self.lands, p)
                messages += result["messages"]
                updated += result.get("updated_players", [])

            elif mode == 2:   # 命運卡
                result = self._fate.operate(self.players, self.lands, p)
                messages += result["messages"]
                updated += result.get("updated_players", [])

            elif mode == 3:   # 商店
                pending = "shop"

            # mode == -1：無功能，不做任何事

        # 更新玩家顯示
        for i in set(updated):
            # 在最終回傳前確保 updated 包含所有受影響玩家
            pass

        bankruptcy = self._bankruptcy_event(updated)
        if bankruptcy["message"]:
            messages.append(bankruptcy["message"])

        self._pending = pending
        self._pending_land_idx = pending_info.get("land_idx")

        return _make_event(
            messages=messages,
            pending=pending,
            pending_info=pending_info,
            game_over=bankruptcy["game_over"],
            loser_name=bankruptcy["loser_name"],
            updated_players=list(set(bankruptcy["updated_players"])),
        )

    def confirm_buy_land(self, yes: bool) -> dict:
        """
        玩家對「購買土地」確認框的回應。
        yes=True → 扣款、標記地主；False → 放棄。
        """
        p = self.current_player_idx
        player = self.players[p]
        loc = self._pending_land_idx
        if self._pending != "buy" or loc is None:
            return _make_event(messages=["No land purchase is pending."], updated_players=[p])
        land = self.lands[loc]

        if yes:
            player.buy_land(land.get_money(), loc)
            land.buy_land(p)
            msg = "已完成購買..."
        else:
            msg = "未完成購買..."

        self._pending = None
        self._pending_land_idx = None

        bankruptcy = self._bankruptcy_event([p])
        messages = [msg]
        if bankruptcy["message"]:
            messages.append(bankruptcy["message"])
        return _make_event(
            messages=messages,
            game_over=bankruptcy["game_over"],
            loser_name=bankruptcy["loser_name"],
            updated_players=bankruptcy["updated_players"],
        )

    def confirm_upgrade_land(self, yes: bool) -> dict:
        """
        玩家對「升級房屋」確認框的回應。
        yes=True → 檢查是否持有 VIP 卡，扣款，升級地產。
        """
        p = self.current_player_idx
        player = self.players[p]
        loc = self._pending_land_idx
        if self._pending != "upgrade" or loc is None:
            return _make_event(messages=["No land upgrade is pending."], updated_players=[p])
        land = self.lands[loc]
        messages = []

        if yes:
            prop = player.get_prop()
            vip_slot = next((i for i, v in enumerate(prop) if v == 3), -1)
            has_vip = vip_slot != -1
            if has_vip:
                messages.append("玩家擁有房產VIP卡（蓋房減免1000元）")
                prop.pop(vip_slot)
            player.upgrade_land(land.get_build(), has_vip=has_vip)
            land.upgrade_land()
            messages.append("已完成升級...")
        # 升級失敗時不輸出訊息，保持既有行為

        self._pending = None
        self._pending_land_idx = None

        bankruptcy = self._bankruptcy_event([p])
        if bankruptcy["message"]:
            messages.append(bankruptcy["message"])
        return _make_event(
            messages=messages,
            game_over=bankruptcy["game_over"],
            loser_name=bankruptcy["loser_name"],
            updated_players=bankruptcy["updated_players"],
        )

    def use_item(self, slot: int) -> dict:
        """
        主動使用玩家道具欄中第 slot 個道具（0-based）。
        目前只有骰子（idx=0）有主動效果。
        額外步數累積到 additional_points，下次 roll_dice 時一併加入。
        """
        p = self.current_player_idx
        player = self.players[p]
        result = self._shop.use_item(slot, player, self.players, self.lands, p)
        self.additional_points += result["extra_points"]
        return _make_event(
            messages=[result["message"]],
            updated_players=[p],
        )

    def get_shop_display(self) -> List[dict]:
        """回傳商店道具資訊列表（供 UI 繪製商店視窗）。"""
        return self._shop.get_shop_display()

    def buy_shop_item(self, item_idx: int) -> dict:
        """在商店視窗中購買一件道具。可多次呼叫。"""
        p = self.current_player_idx
        player = self.players[p]
        result = self._shop.buy(item_idx, player)
        bankruptcy = self._bankruptcy_event([p])
        messages = [result["message"]]
        if bankruptcy["message"]:
            messages.append(bankruptcy["message"])
        return _make_event(
            messages=messages,
            game_over=bankruptcy["game_over"],
            loser_name=bankruptcy["loser_name"],
            updated_players=bankruptcy["updated_players"],
        )

    def close_shop(self) -> dict:
        """關閉商店視窗，清除 pending 狀態。"""
        self._pending = None
        return _make_event(messages=["已離開商店"])

    def end_turn(self) -> dict:
        """
        結束當前回合：重置額外步數，推進到下一位玩家。
        回傳訊息為分隔線。
        """
        self.additional_points = 0
        self.round += 1
        self.current_player_idx = self.round % 4
        return _make_event(
            messages=["--------------------------------------------------------------"],
            updated_players=[self.current_player_idx],
        )

    # ── 狀態查詢（供 UI 初始化與刷新） ───────────────────────────────────────

    def get_player_info(self, player_idx: int) -> dict:
        """回傳指定玩家的完整資訊字典。"""
        if player_idx < 0 or player_idx >= len(self.players):
            raise IndexError(f"Invalid player index: {player_idx}")
        return self.players[player_idx].get_info()

    def get_land_info(self, land_idx: int) -> dict:
        """回傳指定地格的資訊字典。"""
        if land_idx < 0 or land_idx >= BOARD_SIZE:
            raise IndexError(f"Invalid land index: {land_idx}")
        land = self.lands[land_idx]
        return {
            "idx": land_idx,
            "name": land.get_name(),
            "mode": land.get_mode(),
            "price": land.get_money(),
            "build": land.get_build(),
            "owner": land.get_owner(),
            "ownernum": land.get_ownernum(),
            "level": land.get_level(),
        }

    def get_full_state(self) -> dict:
        """
        回傳完整遊戲狀態快照，供 UI 初始化或全面刷新。
        """
        return {
            "round": self.round,
            "current_player": self.current_player_idx,
            "players": [p.get_info() for p in self.players],
            "lands": [self.get_land_info(i) for i in range(BOARD_SIZE)],
            "pending": self._pending,
        }

    # ── 內部邏輯 ──────────────────────────────────────────────────────────────

    def _normal_action(self, p: int, loc: int) -> dict:
        """
        普通格三路判斷：
          1. 無主 → 詢問是否購買
          2. 自己的地 且 level < 4 → 詢問是否升級
          3. 他人的地 → 自動扣租金
        """
        land = self.lands[loc]
        player = self.players[p]
        name = PLAYER_NAMES[p]
        messages = []
        updated = [p]
        pending = None
        pending_info: dict = {}

        if land.get_ownernum() == 0:
            # 無主地
            if player.get_money() >= land.get_money():
                pending = "buy"
                pending_info = {
                    "land_name": land.get_name(),
                    "price": land.get_money(),
                    "land_idx": loc,
                }
            else:
                messages.append("沒錢還想買地啊！窮逼！！！")

        elif land.get_ownernum() == p + 1 and land.get_level() < 4:
            # 自己的地，可升級
            if player.get_money() < land.get_build():
                messages.append("哭哭~你的錢不夠了!")
            else:
                pending = "upgrade"
                pending_info = {
                    "land_name": land.get_name(),
                    "price": land.get_build(),
                    "land_idx": loc,
                }

        elif land.get_ownernum() == p + 1:
            messages.append("此土地已達最高等級")

        else:
            # 他人的地（或自己已滿級）：收租
            owner_idx = land.get_ownernum() - 1
            rent = int(land.get_money() * 0.4)
            messages.append(f"此土地歸屬 {land.get_owner()} 所有")
            messages.append(f"{name} 損失 {rent}")
            messages.append(f"{land.get_owner()} 血賺 {rent}")
            self.players[owner_idx].earn_money(rent)
            player.lose_money(rent)
            messages.append("已完成交易...")
            updated.append(owner_idx)

        return {
            "messages": messages,
            "pending": pending,
            "pending_info": pending_info,
            "updated_players": updated,
        }
