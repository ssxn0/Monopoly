from __future__ import annotations
import random
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player import Player
    from core.land import Land

# ── 卡片基底 ──────────────────────────────────────────────────────────────────

class _Card:
    def action(self, players: List["Player"], lands: List["Land"], p: int) -> dict:
        raise NotImplementedError


# ── 20 張卡片實作 ─────────────────────────────────────────────────────────────

class _Emp(_Card):
    """遇到暗黑大帝（4 張）：擲骰決定得 / 失 2000 元。"""

    def action(self, players, lands, p):
        num = random.randint(2, 12)          # 修正 Bug：不再固定回傳 6
        if num % 2 == 0:
            players[p].earn_money(2000)
            return {
                "messages": [
                    "您遇到了暗黑大帝，請擲骰子，若點數為雙數，則獲得2000元，單數則損失2000元",
                    f"骰出 {num}（雙數），恭喜獲得2000元！"
                ],
                "updated_players": [p],
            }
        else:
            players[p].lose_money(2000)
            return {
                "messages": [
                    "您遇到了暗黑大帝，請擲骰子，若點數為雙數，則獲得2000元，單數則損失2000元",
                    f"骰出 {num}（單數），很遺憾的，您將損失2000元！"
                ],
                "updated_players": [p],
            }


class _FreeHouse(_Card):
    """
    幫隨機玩家免費蓋一棟房子（2 張）。
    """

    def action(self, players, lands, p):
        c = int(random.random()) * 3   # Bug 複製：永遠為 0
        msg = f"恭喜第{c + 1}位玩家可以免費蓋一棟房子!"

        if not players[p].get_house():
            return {"messages": [msg, "（當前玩家無地產，無法蓋房）"], "updated_players": []}

        # 找出當前玩家最便宜的地產並升級
        cheapest_idx = min(
            players[p].get_house(),
            key=lambda idx: lands[idx].get_money()
        )
        lands[cheapest_idx].upgrade_land()
        return {"messages": [msg], "updated_players": [p]}


class _Wolf(_Card):
    """遇到大野狼，損失 3000 元（2 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(3000)
        return {
            "messages": ["您遇到了大野狼，被牠搶走了3000元"],
            "updated_players": [p],
        }


class _Rest(_Card):
    """天黑，休息一回合（2 張）。"""

    def action(self, players, lands, p):
        players[p].rest_round(1)
        return {
            "messages": ["天黑了，看不清前方的路，休息一回合"],
            "updated_players": [p],
        }


class _WaterFood(_Card):
    """找到水源及莓果，獲得 5000 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].earn_money(5000)
        return {
            "messages": ["找到水源及莓果，獲得獎金5000元"],
            "updated_players": [p],
        }


class _Rabbit(_Card):
    """幫助兔子回家，獲得 3000 元（2 張）。"""

    def action(self, players, lands, p):
        players[p].earn_money(3000)
        return {
            "messages": ["幫助兔子找到牠回家的路，獲得獎金3000元"],
            "updated_players": [p],
        }


class _Soil(_Card):
    """
    獎金卡（3 張）。
    """

    def action(self, players, lands, p):
        players[p].earn_money(3000)
        return {
            "messages": ["幫助兔子找到牠回家的路，獲得獎金3000元"],
            "updated_players": [p],
        }


class _FreeHouse1(_Card):
    """跟大老闆成為朋友，免費幫自己蓋一棟房子（1 張）。"""

    def action(self, players, lands, p):
        msg = "您跟大老闆成為了好朋友，他決定免費幫您蓋一棟房子"
        if not players[p].get_house():
            return {"messages": [msg, "（無地產，無法蓋房）"], "updated_players": []}

        cheapest_idx = min(
            players[p].get_house(),
            key=lambda idx: lands[idx].get_money()
        )
        lands[cheapest_idx].upgrade_land()
        return {"messages": [msg], "updated_players": [p]}


class _FreeHouse2(_Card):
    """跟富豪的兒子成為朋友，免費幫自己蓋一棟房子（1 張）。"""

    def action(self, players, lands, p):
        msg = "您跟富豪的兒子成為了好朋友，他決定免費幫您蓋一棟房子"
        if not players[p].get_house():
            return {"messages": [msg, "（無地產，無法蓋房）"], "updated_players": []}

        cheapest_idx = min(
            players[p].get_house(),
            key=lambda idx: lands[idx].get_money()
        )
        lands[cheapest_idx].upgrade_land()
        return {"messages": [msg], "updated_players": [p]}


class _Drop(_Card):
    """睡覺時掉了 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(1500)
        return {
            "messages": ["您在睡覺的時候掉了1500元!"],
            "updated_players": [p],
        }


class _Drop2(_Card):
    """爬樹時掉了 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(1500)
        return {
            "messages": ["您在爬樹的時候掉了1500元!"],
            "updated_players": [p],
        }


# ── 機會卡牌組 ────────────────────────────────────────────────────────────────

class ChanceCard:
    """
    20 張機會卡的牌組，初始化時洗牌，循環抽取。

    卡片分布（對應 Java ChanceCard.java）：
      emp × 4、freeHouse × 2、wolf × 2、rest × 2、
      waterFood × 1、rabbit × 2、soil × 3、
      freeHouse1 × 1、freeHouse2 × 1、drop × 1、drop2 × 1
    """

    def __init__(self) -> None:
        deck: List[_Card] = (
            [_Emp()] * 4
            + [_FreeHouse()] * 2
            + [_Wolf()] * 2
            + [_Rest()] * 2
            + [_WaterFood()]
            + [_Rabbit()] * 2
            + [_Soil()] * 3
            + [_FreeHouse1()]
            + [_FreeHouse2()]
            + [_Drop()]
            + [_Drop2()]
        )
        random.shuffle(deck)
        self._deck: List[_Card] = deck
        self._index: int = 0

    def operate(self, players: List["Player"], lands: List["Land"], p: int) -> dict:
        """抽一張卡並執行效果，回傳事件字典。"""
        result = self._deck[self._index].action(players, lands, p)
        self._index = (self._index + 1) % len(self._deck)
        return result
