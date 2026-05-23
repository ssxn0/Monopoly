import random


class Dice:
    """模擬一顆標準骰子（點數 1–6），兩顆合計 2–12。"""

    def rotate(self) -> int:
        """擲骰子，回傳 2 到 12 的隨機整數。

        原版 Java 使用預先建立的陣列再 shuffle，
        Python 版直接用 random.randint 達到同等效果。
        """
        return random.randint(1, 6) + random.randint(1, 6)
