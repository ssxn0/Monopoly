"""整合測試：模擬 3 個完整回合。"""
import sys
sys.path.insert(0, ".")

from core.game_state import GameState

gs = GameState()
print("=== 整合測試：模擬 3 個完整回合 ===")
print(f"棋盤格數: {len(gs.lands)}")
print(f"玩家: {[p.name for p in gs.players]}")
print()

for turn in range(3):
    ev = gs.start_round()
    cur = gs.players[gs.current_player_idx]
    print(f"--- 回合 {gs.round} | 玩家 {cur.name} ---")
    for m in ev["messages"]:
        print(f"  [{m}]")

    if ev["pending"] == "skip":
        gs.end_turn()
        continue

    # 擲骰
    ev = gs.roll_dice()
    for m in ev["messages"]:
        print(f"  [{m}]")

    if ev["game_over"]:
        print(f"  >> 遊戲結束！{ev['loser_name']} 破產")
        break

    # 處理 pending
    if ev["pending"] == "buy":
        info = ev["pending_info"]
        print(f"  >> 詢問購買: {info['land_name']} ${info['price']}")
        ev2 = gs.confirm_buy_land(True)
        for m in ev2["messages"]:
            print(f"  [{m}]")

    elif ev["pending"] == "upgrade":
        info = ev["pending_info"]
        print(f"  >> 詢問升級: {info['land_name']} ${info['price']}")
        ev2 = gs.confirm_upgrade_land(True)
        for m in ev2["messages"]:
            print(f"  [{m}]")

    elif ev["pending"] == "shop":
        print("  >> 進入商店")
        for item in gs.get_shop_display():
            print(f"     {item['name']} ${item['price']}")
        ev2 = gs.buy_shop_item(0)  # 購買骰子
        for m in ev2["messages"]:
            print(f"  [{m}]")
        gs.close_shop()

    # 顯示玩家狀態
    info = gs.get_player_info(gs.current_player_idx)
    print(f"  >> 金錢={info['money']}  地產={info['house_count']}  "
          f"道具={info['prop_count']}  位置={info['locate']}")

    gs.end_turn()

print()

# 額外測試：use_item 骰子加成
print("=== 道具加成測試 ===")
gs2 = GameState()
gs2.players[0].get_prop().append(0)  # 手動給骰子
ev = gs2.use_item(0)
print(f"使用骰子道具訊息: {ev['messages']}")
print(f"額外步數: {gs2.additional_points}")
assert gs2.additional_points >= 1

# 額外測試：監獄流程
print()
print("=== 監獄流程測試 ===")
gs3 = GameState()
player0 = gs3.players[0]
player0.move_to_jail()
player0.rest_round(1)
assert player0.is_in_jail()
ev = gs3.start_round()
print(f"監獄回合: {ev['messages']}")
assert ev["pending"] == "skip"

print()
print("=== 全部整合測試通過 ===")
