PLAYER_NAMES = ["布魯", "瑞德", "椰柔", "古林"]


class Land:
    """代表棋盤上的一格地產。"""

    def __init__(self, name: str, price: int, mode: int) -> None:
        self.name: str = name
        self.mode: int = mode          # 地格類型
        self.money: int = price        # 售價 / 罰款基準
        self.build: int = int(price * 0.6)  # 蓋房子費用
        self.owner: str = ""           # 擁有者名稱
        self.ownernum: int = 0         # 擁有者編號（1–4，0 代表無主）
        self.level: int = 1            # 房屋等級（1 = 空地，最高 4）

    # ── Getters ────────────────────────────────────────────────────────────

    def get_name(self) -> str:
        return self.name

    def get_mode(self) -> int:
        return self.mode

    def get_money(self) -> int:
        return self.money

    def get_build(self) -> int:
        return self.build

    def get_owner(self) -> str:
        return self.owner

    def get_ownernum(self) -> int:
        return self.ownernum

    def get_level(self) -> int:
        return self.level

    # ── 狀態變更 ───────────────────────────────────────────────────────────

    def buy_land(self, player_idx: int) -> None:
        """標記土地擁有者。player_idx 為 0–3。"""
        self.owner = PLAYER_NAMES[player_idx]
        self.ownernum = player_idx + 1

    def upgrade_land(self) -> None:
        """升級房屋：售價 += 蓋房費，等級 +1。"""
        self.money += self.build
        self.level += 1

    def degrade_land(self) -> None:
        """拆除房屋：售價 -= 蓋房費，等級 -1。"""
        self.money -= self.build
        self.level -= 1

    def __repr__(self) -> str:
        return (f"Land({self.name!r}, price={self.money}, mode={self.mode}, "
                f"owner={self.owner!r}, level={self.level})")
