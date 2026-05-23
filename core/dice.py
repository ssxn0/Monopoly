import random


class Dice:
    """模擬一顆標準骰子（點數 1–6），兩顆合計 2–12。"""

    def rotate(self) -> int:
        """擲骰子，回傳 2 到 12 的隨機整數。

        直接用 random.randint 產生兩顆骰子的合計點數。
        """
        return random.randint(1, 6) + random.randint(1, 6)
