from __future__ import annotations
import json
import random
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.player import Player
    from core.land import Land

# ── 道具定義 ──────────────────────────────────────────────────────────────────

class Prop:
    """道具基底類別。"""

    def __init__(self, idx: int, name: str, price: int, info: str) -> None:
        self.idx = idx
        self.name = name
        self.price = price
        self.info = info

    def get_name(self) -> str:
        return self.name

    def get_price(self) -> int:
        return self.price

    def get_information(self) -> str:
        return self.info

    def use(self, players: List["Player"], lands: List["Land"], p: int) -> int:
        """
        主動使用效果（目前只有骰子道具需要此方法）。
        回傳額外步數（0 代表無效果）。
        """
        return 0

    def __repr__(self) -> str:
        return f"Prop({self.name}, ${self.price})"


class _Dice(Prop):
    """骰子：主動使用，額外擲 1–6 步。"""

    def use(self, players, lands, p) -> int:
        extra = random.randint(1, 6)
        return extra


# ── 商店 ─────────────────────────────────────────────────────────────────────

class Shop:
    """
    管理 5 種道具的資料與購買邏輯。
    UI 層呼叫 get_props() 取得清單後自行顯示，
    玩家選擇購買時呼叫 buy(item_idx, player, messages)。
    """

    _ITEMS_FILE = Path(__file__).parent.parent / "data" / "items.json"

    def __init__(self) -> None:
        self._props: List[Prop] = self._build_props()

    def _build_props(self) -> List[Prop]:
        # 嘗試從 JSON 讀取，若找不到則使用硬編碼資料（確保可獨立運作）
        try:
            data = json.loads(self._ITEMS_FILE.read_text(encoding="utf-8"))
            props = []
            for item in sorted(data, key=lambda d: d["idx"]):
                if item["idx"] == 0:
                    props.append(_Dice(item["idx"], item["name"], item["price"], item["info"]))
                else:
                    props.append(Prop(item["idx"], item["name"], item["price"], item["info"]))
            return props
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            # Fallback：硬編碼資料
            return [
                _Dice(0, "骰子",     1300, "骰子\n\n選取道具後可多擲一顆骰子"),
                Prop(1, "健保卡",    1500, "健保卡\n\n醫藥費補助1800元"),
                Prop(2, "免獄卡",    1800, "免獄卡\n\n可直接出獄"),
                Prop(3, "房產VIP卡",  900, "房產VIP卡\n\n下次蓋房子可減少1000元"),
                Prop(4, "恭喜出獄卡", 1300, "恭喜出獄卡\n\n入獄時可獲得補助1500元"),
            ]

    # ── 公開 API ──────────────────────────────────────────────────────────────

    def get_props(self) -> List[Prop]:
        """回傳所有道具列表（供 UI 顯示）。"""
        return self._props

    def get_prop(self, idx: int) -> Prop:
        """以道具編號取得道具物件。"""
        return self._props[idx]

    def buy(self, item_idx: int, player: "Player") -> dict:
        """
        購買指定道具。
        回傳 {"success": bool, "message": str}
        """
        prop = self._props[item_idx]
        if player.get_money() >= prop.get_price():
            player.lose_money(prop.get_price())
            player.get_prop().append(item_idx)
            return {"success": True, "message": f"已購買{prop.get_name()}"}
        else:
            return {"success": False, "message": "沒錢了還想買啊！！！"}

    def use_item(self, slot: int, player: "Player",
                 players: List["Player"], lands: List["Land"], p: int) -> dict:
        """
        使用玩家道具欄中第 slot 個道具（主動型）。
        目前只有骰子（idx=0）可主動使用。
        回傳 {"extra_points": int, "message": str, "used": bool}
        """
        prop_list = player.get_prop()
        if slot < 0 or slot >= len(prop_list):
            return {"extra_points": 0, "message": "無效的道具槽", "used": False}

        item_idx = prop_list[slot]
        prop = self._props[item_idx]

        if item_idx == 0:   # 骰子道具
            extra = prop.use(players, lands, p)
            prop_list.pop(slot)
            return {
                "extra_points": extra,
                "message": f"{player.name}使用了{prop.get_name()}（額外 {extra} 步）",
                "used": True,
            }
        else:
            return {
                "extra_points": 0,
                "message": f"{prop.get_name()}為被動道具，無需手動使用",
                "used": False,
            }

    def get_shop_display(self) -> List[dict]:
        """回傳商店顯示資訊列表，供 UI 繪製商店視窗。"""
        return [
            {"idx": p.idx, "name": p.name, "price": p.price, "info": p.info}
            for p in self._props
        ]
