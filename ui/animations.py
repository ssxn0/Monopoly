from __future__ import annotations

import math
import random
import pygame

from ui.board_renderer import BoardRenderer, get_sprite_pos
from ui.constants import (
    FPS,
    PARCHMENT,
    PARCHMENT_DARK,
    SCREEN_H,
    SCREEN_W,
    SHADOW,
    TURN_GLOW,
)
from ui.utils import draw_rect_alpha

if False:
    from core.game_state import GameState
    from ui.info_panel import InfoPanel


DICE_ROLL_MS = 850
STEP_MS = 280
SPECIAL_STEP_MS = 240


def draw_dice_face(
    surface: pygame.Surface,
    value: int,
    rect: pygame.Rect,
    angle: float = 0.0,
) -> None:
    dice = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(dice, (245, 238, 220), dice.get_rect(), border_radius=14)
    pygame.draw.rect(dice, PARCHMENT_DARK, dice.get_rect(), 3, border_radius=14)

    pip_radius = max(5, rect.width // 13)
    pad_x = rect.width * 0.27
    pad_y = rect.height * 0.27
    centers = {
        "tl": (pad_x, pad_y),
        "tc": (rect.width / 2, pad_y),
        "tr": (rect.width - pad_x, pad_y),
        "ml": (pad_x, rect.height / 2),
        "mc": (rect.width / 2, rect.height / 2),
        "mr": (rect.width - pad_x, rect.height / 2),
        "bl": (pad_x, rect.height - pad_y),
        "bc": (rect.width / 2, rect.height - pad_y),
        "br": (rect.width - pad_x, rect.height - pad_y),
    }
    patterns = {
        1: ["mc"],
        2: ["tl", "br"],
        3: ["tl", "mc", "br"],
        4: ["tl", "tr", "bl", "br"],
        5: ["tl", "tr", "mc", "bl", "br"],
        6: ["tl", "ml", "bl", "tr", "mr", "br"],
    }
    for key in patterns[value]:
        pygame.draw.circle(dice, SHADOW, centers[key], pip_radius)

    if angle:
        dice = pygame.transform.rotate(dice, angle)
    surface.blit(dice, dice.get_rect(center=rect.center))


def animate_dice_roll(
    screen: pygame.Surface,
    renderer: "BoardRenderer",
    gs: "GameState",
    info_panel: "InfoPanel",
    final_total: int,
    draw_hud,
) -> None:
    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    left = pygame.Rect(SCREEN_W // 2 - 95, SCREEN_H // 2 - 48, 74, 74)
    right = pygame.Rect(SCREEN_W // 2 + 21, SCREEN_H // 2 - 48, 74, 74)

    if final_total <= 12:
        d1 = max(1, min(6, final_total // 2))
        d2 = max(1, min(6, final_total - d1))
    else:
        d1, d2 = 6, 6

    while True:
        elapsed = pygame.time.get_ticks() - start
        done = elapsed >= DICE_ROLL_MS
        if done:
            a, b = d1, d2
        else:
            a, b = random.randint(1, 6), random.randint(1, 6)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        renderer.draw(gs)
        info_panel.draw()
        draw_hud(screen, gs, pygame.mouse.get_pos())

        draw_rect_alpha(screen, (0, 0, 0), (0, 0, SCREEN_W, SCREEN_H), 70)
        wobble = math.sin(elapsed / 55) * 12
        draw_dice_face(screen, a, left.move(int(math.sin(elapsed / 95) * 10), 0), elapsed * 0.55 + wobble)
        draw_dice_face(screen, b, right.move(int(math.cos(elapsed / 90) * 10), 0), -elapsed * 0.5 + wobble)
        pygame.display.flip()
        clock.tick(FPS)
        if done:
            pygame.time.delay(180)
            return


def build_path(start: int, end: int, steps: int | None = None) -> list[int]:
    if start == end:
        return []
    if steps is not None and start < 48:
        direction = 1 if steps >= 0 else -1
        path = [((start + direction * i) % 48) for i in range(1, abs(steps) + 1)]
        if path and path[-1] != end:
            path.append(end)
        return path
    if start < 48 and end < 48:
        forward = (end - start) % 48
        backward = (start - end) % 48
        if forward <= backward:
            return [((start + i) % 48) for i in range(1, forward + 1)]
        return [((start - i) % 48) for i in range(1, backward + 1)]
    if end >= 48:
        return [end]
    return [end]


def animate_player_path(
    screen: pygame.Surface,
    renderer: "BoardRenderer",
    gs: "GameState",
    info_panel: "InfoPanel",
    player_idx: int,
    path: list[int],
    draw_hud,
    step_ms: int = STEP_MS,
) -> None:
    if not path:
        return

    player = gs.players[player_idx]
    final_loc = player.locate
    current = player.locate
    visual_locs = {player_idx: current}
    clock = pygame.time.Clock()

    for target in path:
        start_pos = get_sprite_pos(current, player_idx)
        end_pos = get_sprite_pos(target, player_idx)
        step_start = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - step_start
            t = min(1.0, elapsed / step_ms)
            eased = 1 - (1 - t) * (1 - t)
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * eased
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * eased
            bounce = math.sin(t * math.pi) * 18
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            renderer.draw(
                gs,
                animated_positions={player_idx: (x, y - bounce)},
                visual_locs=visual_locs,
            )
            info_panel.draw()
            draw_hud(screen, gs, pygame.mouse.get_pos())
            pygame.display.flip()
            clock.tick(FPS)
            if t >= 1.0:
                break

        current = target
        visual_locs[player_idx] = current
        pygame.time.delay(45)

    player.locate = final_loc


def play_roll_sequence(
    screen: pygame.Surface,
    renderer: "BoardRenderer",
    gs: "GameState",
    info_panel: "InfoPanel",
    movement: dict,
    draw_hud,
) -> None:
    if not movement:
        return
    player_idx = movement["player"]
    player = gs.players[player_idx]
    final_loc = player.locate

    player.locate = movement["from"]
    animate_dice_roll(screen, renderer, gs, info_panel, movement["points"], draw_hud)

    dice_path = build_path(movement["from"], movement["dice_to"], movement["points"])
    animate_player_path(screen, renderer, gs, info_panel, player_idx, dice_path, draw_hud)

    if movement["final_to"] != movement["dice_to"]:
        player.locate = movement["dice_to"]
        special_path = build_path(movement["dice_to"], movement["final_to"])
        animate_player_path(
            screen,
            renderer,
            gs,
            info_panel,
            player_idx,
            special_path,
            draw_hud,
            step_ms=SPECIAL_STEP_MS,
        )

    player.locate = final_loc
