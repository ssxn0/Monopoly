from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.land import Land

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]
STARTING_MONEY = 100_000
GO_BONUS = 2_000


class Player:
    """代表一位大富翁玩家，追蹤位置、金錢、房產與道具。"""

    def __init__(self, number: int) -> None:
        """
        number: 玩家編號，1–4。
        """
        self.number: int = number
        self.name: str = PLAYER_NAMES[number - 1]

        self.locate: int = 0           # 目前位置索引
        self.money: int = STARTING_MONEY
        self.stop_round: int = 0       # 剩餘暫停回合數（醫院 / 監獄）

        # 持有的地產（land 索引列表）與道具（item 索引列表）
        self.house: List[int] = []
        self.prop: List[int] = []

    # ── Getters ────────────────────────────────────────────────────────────

    def get_money(self) -> int:
        return self.money

    def get_locate(self) -> int:
        return self.locate

    def get_house(self) -> List[int]:
        return self.house

    def get_prop(self) -> List[int]:
        return self.prop

    # ── 移動邏輯 ────────────────────────────────────────────────────────────

    def move(self, m: int) -> int:
        """
        移動玩家 m 步，回傳新位置索引。

        正數 m：前進；負數 m：因原始運算方式
        (this.locate - m，m 為負數 → 實際 +|m|) 會往前移。

        特殊區段：
          48–52 醫院：先扣 stop_round，歸零後才離開醫院。
          53–56 監獄：先扣 stop_round，歸零後才離開監獄。
        """
        if m > 0:
            if self.locate < 48:
                # 過起點獎勵
                if self.locate + m > 48:
                    self.money += GO_BONUS
                self.locate = (self.locate + m) % 48
                self._check_river()

            elif 48 <= self.locate <= 52:
                # 醫院區
                if self.stop_round > 0:
                    self.stop_round -= 1
                else:
                    if self.locate + m > 52:
                        # 離開醫院，重回棋盤（從第 45 格之後接回）
                        self.locate = (45 + (self.locate + m - 53)) % 48
                    else:
                        self.locate += m

            elif 53 <= self.locate <= 56:
                # 監獄區
                if self.stop_round > 0:
                    self.stop_round -= 1
                else:
                    if self.locate + m > 56:
                        # 離開監獄，重回棋盤（從第 12 格之後接回）
                        self.locate = 12 + (self.locate + m - 57)
                    else:
                        self.locate += m

        elif m < 0:
            # 例：move(-2) 實際讓 locate 增加 2（往前走）
            self.locate = self.locate - m
            if self.locate < 0:
                self.locate = 48 + self.locate
            self._check_river()

        return self.locate

    def _check_river(self) -> None:
        """溪流判定：落在格 29（瀑布上游）→ 傳送至格 15（瀑布下游）。"""
        if self.locate == 29:
            self.locate = 15

    # ── 特殊位置傳送 ───────────────────────────────────────────────────────

    def move_to_jail(self) -> None:
        """入獄（位置設為 56）。"""
        self.locate = 56

    def out_from_jail(self) -> None:
        """出獄（位置設為 55，stop_round 清零）。"""
        self.stop_round = 0
        self.locate = 55

    def move_to_hospital(self) -> None:
        """進醫院（位置設為 52）。"""
        self.locate = 52

    # ── 財務操作 ───────────────────────────────────────────────────────────

    def earn_money(self, amount: int) -> None:
        """增加金錢。"""
        self.money += amount

    def lose_money(self, amount: int) -> None:
        """減少金錢。"""
        self.money -= amount

    def buy_land(self, price: int, land_idx: int) -> None:
        """購買地產：扣款並記錄持有地索引。"""
        self.money -= price
        self.house.append(land_idx)

    def upgrade_land(self, price: int, has_vip: bool = False) -> None:
        """
        升級房屋：扣款。
        has_vip=True 時使用房產VIP卡（減免 1000 元），
        呼叫前應從 prop 移除該卡。
        """
        if has_vip:
            price -= 1000
        self.money -= price

    def rest_round(self, amount: int) -> None:
        """增加暫停回合數（醫院 / 霧等狀態）。"""
        self.stop_round += amount

    # ── 狀態查詢 ───────────────────────────────────────────────────────────

    def is_bankrupt(self) -> bool:
        """金錢 ≤ 0 時視為破產。"""
        return self.money <= 0

    def is_on_board(self) -> bool:
        """是否在主棋盤（0–47）上。"""
        return self.locate < 48

    def is_in_hospital(self) -> bool:
        return 48 <= self.locate <= 52

    def is_in_jail(self) -> bool:
        return 53 <= self.locate <= 56

    def get_info(self) -> dict:
        """回傳玩家資訊字典，供 UI 層更新顯示。"""
        return {
            "number": self.number,
            "name": self.name,
            "money": self.money,
            "house_count": len(self.house),
            "prop_count": len(self.prop),
            "locate": self.locate,
            "stop_round": self.stop_round,
        }

    def __repr__(self) -> str:
        status = "監獄" if self.is_in_jail() else "醫院" if self.is_in_hospital() else f"格{self.locate}"
        return f"Player({self.name}, 金錢={self.money}, 位置={status})"
