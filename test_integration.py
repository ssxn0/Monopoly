"""整合測試：模擬 3 個完整回合。"""
import sys
sys.path.insert(0, ".")

from core.game_state import GameState
from core.chance_card import _FreeHouse, _Rest
from core.fate_card import _Fog, _RemoveHouse
from core.player import Player
import core.chance_card as chance_card
import core.fate_card as fate_card

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
print("=== Bug regression tests ===")

p = Player(1)
p.locate = 10
p.move(-3)
print(f"move(-3) from 10 -> {p.locate}")
assert p.locate == 7

p2 = Player(1)
p2.locate = 47
p2.move(1)
assert p2.locate == 0
assert p2.money == 102000

gs4 = GameState()
gs4.players[2].get_house().append(1)
before_price = gs4.lands[1].get_money()
old_chance_randrange = chance_card.random.randrange
try:
    chance_card.random.randrange = lambda n: 2
    _FreeHouse().action(gs4.players, gs4.lands, 0)
    assert gs4.lands[1].get_money() > before_price
finally:
    chance_card.random.randrange = old_chance_randrange

gs4b = GameState()
land = gs4b.lands[1]
land.buy_land(0)
gs4b.players[0].get_house().append(1)
while land.get_level() < 4:
    land.upgrade_land()
old_chance_randrange = chance_card.random.randrange
try:
    chance_card.random.randrange = lambda n: 0
    _FreeHouse().action(gs4b.players, gs4b.lands, 0)
    assert land.get_level() == 4
finally:
    chance_card.random.randrange = old_chance_randrange

old_randrange = fate_card.random.randrange
try:
    for selected in [0, 1, 2, 3]:
        fate_card.random.randrange = lambda n, selected=selected: selected
        gs5 = GameState()
        _RemoveHouse().action(gs5.players, gs5.lands, 0)
        changed = [i for i, player in enumerate(gs5.players) if player.get_money() != 100000]
        assert changed == [selected]
finally:
    fate_card.random.randrange = old_randrange

gs6 = GameState()
gs6.players[1].money = 1000
gs6._dice.rotate = lambda: 5
gs6._fate._deck = [_Fog()]
gs6._fate._index = 0
ev = gs6.roll_dice()
assert ev["game_over"] is True
assert ev["loser_name"] == gs6.players[1].name

gs7 = GameState()
ev = gs7.confirm_buy_land(True)
assert ev["game_over"] is False
assert "pending" in ev["messages"][0]

gs8 = GameState()
land = gs8.lands[1]
land.buy_land(0)
gs8.players[0].get_house().append(1)
gs8.players[0].money = land.get_build()
gs8._pending = "upgrade"
gs8._pending_land_idx = 1
ev = gs8.confirm_upgrade_land(True)
assert ev["game_over"] is True

gs9 = GameState()
price = gs9.get_shop_display()[0]["price"]
gs9.players[0].money = price
gs9._pending = "shop"
ev = gs9.buy_shop_item(0)
assert ev["game_over"] is True

gs10 = GameState()
gs10._pending = "shop"
ev = gs10.buy_shop_item(-1)
assert ev["game_over"] is False
assert gs10.players[0].get_prop() == []
ev = gs10.buy_shop_item(99)
assert ev["game_over"] is False
assert gs10.players[0].get_prop() == []

gs13 = GameState()
ev = gs13.buy_shop_item(0)
assert ev["game_over"] is False
assert gs13.players[0].get_prop() == []
gs13._pending = "shop"
ev = gs13.buy_shop_item(0)
assert ev["game_over"] is False
assert gs13.players[0].get_prop() == [0]
money_after_first_buy = gs13.players[0].get_money()
ev = gs13.buy_shop_item(1)
assert ev["game_over"] is False
assert gs13.players[0].get_prop() == [0]
assert gs13.players[0].get_money() == money_after_first_buy

gs14 = GameState()
_Rest().action(gs14.players, gs14.lands, 0)
ev = gs14.start_round()
assert ev["pending"] == "skip"
assert gs14.players[0].stop_round == 0

for bad_idx in [-1, 4]:
    try:
        gs10.get_player_info(bad_idx)
        raise AssertionError("invalid player index should fail")
    except IndexError:
        pass

for bad_idx in [-1, 48]:
    try:
        gs10.get_land_info(bad_idx)
        raise AssertionError("invalid land index should fail")
    except IndexError:
        pass

gs11 = GameState()
land = gs11.lands[1]
land.buy_land(0)
gs11.players[0].get_house().append(1)
while land.get_level() < 4:
    land.upgrade_land()
before_money = gs11.players[0].get_money()
ev = gs11._normal_action(0, 1)
assert gs11.players[0].get_money() == before_money
assert ev["updated_players"] == [0]

gs12 = GameState()
price = gs12.lands[1].get_money()
gs12.players[0].money = price
ev = gs12._normal_action(0, 1)
assert ev["pending"] == "buy"

print("=== Bug regression tests passed ===")
print("=== 全部整合測試通過 ===")
