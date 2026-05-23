from __future__ import annotations
import random
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player import Player
    from core.land import Land

PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]


# ── 卡片基底 ──────────────────────────────────────────────────────────────────

class _Card:
    def action(self, players: List["Player"], lands: List["Land"], p: int) -> dict:
        raise NotImplementedError


# ── 19 張卡片實作 ─────────────────────────────────────────────────────────────

class _Fog(_Card):
    """大霧，每位玩家損失 2000 元（1 張）。"""

    def action(self, players, lands, p):
        for player in players:
            player.lose_money(2000)
        return {
            "messages": ["每位玩家遭遇大霧，損失2000元"],
            "updated_players": [0, 1, 2, 3],
        }


class _Hurricane(_Card):
    """龍捲風，每位玩家損失 2000 元（1 張）。"""

    def action(self, players, lands, p):
        for player in players:
            player.lose_money(2000)
        return {
            "messages": ["每位玩家遭遇龍捲風，損失2000元"],
            "updated_players": [0, 1, 2, 3],
        }


class _Fire1(_Card):
    """森林大火，當前玩家損失 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(1500)
        return {
            "messages": ["您遇到森林大火，損失1500元"],
            "updated_players": [p],
        }


class _Fire2(_Card):
    """見義勇為，當前玩家獲得 3000 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].earn_money(3000)
        return {
            "messages": ["您遇到森林大火，見義勇為，獲得獎金3000元"],
            "updated_players": [p],
        }


class _Back(_Card):
    """
    後退（2 張）。
    文字：「後退三格」，呼叫 move(-2)。
    """

    def action(self, players, lands, p):
        players[p].move(-3)
        return {
            "messages": ["前方有水坑，立即後退三格"],
            "updated_players": [p],
        }


class _Forward(_Card):
    """前方有熊，往前五格（1 張）。"""

    def action(self, players, lands, p):
        players[p].move(5)
        return {
            "messages": ["您發現後方有熊正追著您跑，往前五格"],
            "updated_players": [p],
        }


class _Forward2(_Card):
    """前方有蜜蜂，往前五格（1 張）。"""

    def action(self, players, lands, p):
        players[p].move(5)
        return {
            "messages": ["您發現後方有蜜蜂正追著您跑，往前五格"],
            "updated_players": [p],
        }


class _Jail(_Card):
    """
    入獄（2 張）。
    若持有免獄卡（prop idx=2）→ 直接消耗免獄卡免受入獄。
    若持有恭喜出獄卡（prop idx=4）→ 入獄但獲得 1500 元補助。
    """

    def action(self, players, lands, p):
        messages = ["您是嫌疑犯，立即入獄"]
        players[p].move_to_jail()

        prop = players[p].get_prop()
        idx2 = next((i for i, v in enumerate(prop) if v == 2), -1)
        idx4 = next((i for i, v in enumerate(prop) if v == 4), -1)

        if idx2 != -1:
            messages.append("玩家擁有免獄卡")
            prop.pop(idx2)
        elif idx4 != -1:
            messages.append("玩家擁有入獄補助（獲得1500元）")
            prop.pop(idx4)
            players[p].earn_money(1500)

        return {"messages": messages, "updated_players": [p]}


class _Release(_Card):
    """在獄中表現良好，獲得出獄卡（prop idx=2）（2 張）。"""

    def action(self, players, lands, p):
        players[p].get_prop().append(2)
        return {
            "messages": ["您在獄裡表現良好，獲得出獄卡"],
            "updated_players": [p],
        }


class _RemoveHouse(_Card):
    """
    政府下令拆房子（2 張）。
    原版 Bug：c = int(random.random()) * 3 恆為 0，永遠針對玩家 0。
    """

    def action(self, players, lands, p):
        c = random.randrange(len(players))
        messages = [f"政府下令，須拆除玩家{c + 1}的房子"]

        if not players[c].get_house():
            players[c].lose_money(500)
            messages.append("很遺憾地，因為您沒有房產，政府將向您徵求500元")
            return {"messages": messages, "updated_players": [c]}

        # 找可拆除（level > 1）的最便宜地產
        target_idx = None
        min_price = 50_000
        for land_idx in players[c].get_house():
            land = lands[land_idx]
            if land.get_money() < min_price and land.get_level() > 1:
                min_price = land.get_money()
                target_idx = land_idx

        if target_idx is None:
            messages.append("很遺憾地，因為您沒有房子，政府將向您徵求500元")
            players[c].lose_money(500)
        else:
            lands[target_idx].degrade_land()

        return {"messages": messages, "updated_players": [c]}


class _Hospital(_Card):
    """被熊咬傷，進醫院（1 張）。持有健保卡（prop idx=1）→ 獲得 1800 元補助。"""

    def __init__(self, reason: str = "熊") -> None:
        self._reason = reason

    def action(self, players, lands, p):
        messages = [f"您被{self._reason}咬傷了，立即進醫院"]
        players[p].move_to_hospital()

        prop = players[p].get_prop()
        idx1 = next((i for i, v in enumerate(prop) if v == 1), -1)
        if idx1 != -1:
            messages.append("玩家擁有入院補助（獲得1800元）")
            prop.pop(idx1)
            players[p].earn_money(1800)

        return {"messages": messages, "updated_players": [p]}


class _Road(_Card):
    """在路上撿到 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].earn_money(1500)
        return {
            "messages": ["您在路上撿到1500元，並占為己有"],
            "updated_players": [p],
        }


class _Drop(_Card):
    """爬樹時掉了 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(1500)
        return {
            "messages": ["您在爬樹的時候掉了1500元!"],
            "updated_players": [p],
        }


class _Drop2(_Card):
    """睡覺時掉了 1500 元（1 張）。"""

    def action(self, players, lands, p):
        players[p].lose_money(1500)
        return {
            "messages": ["您在睡覺的時候掉了1500元!"],
            "updated_players": [p],
        }


# ── 命運卡牌組 ────────────────────────────────────────────────────────────────

class FateCard:
    """
    19 張命運卡的牌組，初始化時洗牌，循環抽取。

    卡片分布：
      fog×1、hurricane×1、fire1×1、fire2×1、back×2、
      forward×1、forward2×1、jail×2、release×2、
      removeHouse×2、hospital（熊）×1、hospital（蛇）×1、
      road×1、drop×1、drop2×1
    """

    def __init__(self) -> None:
        deck: List[_Card] = [
            _Fog(),
            _Hurricane(),
            _Fire1(),
            _Fire2(),
            _Back(), _Back(),
            _Forward(),
            _Forward2(),
            _Jail(), _Jail(),
            _Release(), _Release(),
            _RemoveHouse(), _RemoveHouse(),
            _Hospital("熊"),
            _Hospital("蛇"),
            _Road(),
            _Drop(),
            _Drop2(),
        ]
        random.shuffle(deck)
        self._deck: List[_Card] = deck
        self._index: int = 0

    def operate(self, players: List["Player"], lands: List["Land"], p: int) -> dict:
        """抽一張卡並執行效果，回傳事件字典。"""
        result = self._deck[self._index].action(players, lands, p)
        # 因牌組長度為 19（index 0–18），修正後使用 modulo
        self._index = (self._index + 1) % len(self._deck)
        return result
