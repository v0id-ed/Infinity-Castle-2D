import pygame
import sys
import random
import math

pygame.init()
pygame.font.init()

# =========================
# SCREEN SETTINGS
# =========================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Infinity Castle 2D")

# =========================
# COLORS
# =========================
RED = (200, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLOOR_COLOR = (139, 0, 0)
STAIR_COLOR = (255, 69, 0)
WALL_BROWNS = [(139, 69, 19), (160, 82, 45), (101, 67, 33)]

# =========================
# TILE / PLAYER SETTINGS
# =========================
TILE_SIZE = 64
player_size = 32
player_speed = 5

# =========================
# PIXEL FONT SETUP
# =========================
FONT_PATH = "PixeloidSans.ttf"
small_font = pygame.font.Font(FONT_PATH, 24)
font = pygame.font.Font(FONT_PATH, 36)
large_font = pygame.font.Font(FONT_PATH, 48)
super_large_font = pygame.font.Font(FONT_PATH, 60)

# =========================
# IMAGE LOADING
# =========================
player_icon = pygame.image.load("Tanjiro.jpg")
player_icon = pygame.transform.smoothscale(player_icon, (player_size, player_size))

muzan_icon = pygame.image.load("Muzan.jpg")
muzan_icon = pygame.transform.smoothscale(muzan_icon, (player_size, player_size))

# Intro background
image = pygame.image.load("Infinity Castle.png")
img_width, img_height = image.get_size()
scale = max(SCREEN_WIDTH / img_width, SCREEN_HEIGHT / img_height)
new_size = (int(img_width * scale), int(img_height * scale))
scaled_image = pygame.transform.smoothscale(image, new_size)
img_x = (new_size[0] - SCREEN_WIDTH) // 2
img_y = (new_size[1] - SCREEN_HEIGHT) // 2
image = scaled_image.subsurface((img_x, img_y, SCREEN_WIDTH, SCREEN_HEIGHT)).copy()

# =========================
# GAME STATE VARIABLES
# =========================
player_x = 0
player_y = 0
player_floor = 0
kimetsu_points = 0

muzan_x = 0
muzan_y = 0
muzan_floor = 0
muzan_health = 12000
muzan_active = False

stair_portal_x = None
stair_portal_y = None
floor_changed = False

castle_map = {}
orange_cubes_map = {}
collected_set = set()
collectible_map = {}
twist_offset = 0
game_seed = None


# =========================
# CENTERED PIXEL TEXT
# =========================
def draw_text_with_outline(text, font_obj, text_color, outline_color, center_x, center_y, surface):
    text_surface = font_obj.render(text, True, text_color)
    outline_surface = font_obj.render(text, True, outline_color)
    text_rect = text_surface.get_rect(center=(center_x, center_y))

    # reduced outline strength (subtle pixel border)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                surface.blit(outline_surface, text_rect.move(dx, dy))

    surface.blit(text_surface, text_rect)


# =========================
# COLLECTIBLE CACHE (ensures consistent rendering)
collectible_map = {}
# (kept simple: deterministic collectibles without extra caching bugs)
# =========================
def get_tile(x, y, floor):
    global castle_map, game_seed

    if (x, y, floor) not in castle_map:
        seed = f"{game_seed}-{x},{y},{floor}" if game_seed else f"default-{x},{y},{floor}"
        rng = random.Random(seed)
        r = rng.random()

        if r < 0.1:
            tile_type = 1
            floor_color = rng.choice(WALL_BROWNS)
        elif r < 0.12:
            tile_type = 2
            floor_color = None
        else:
            tile_type = 0
            floor_color = (
                max(0, min(255, FLOOR_COLOR[0] + rng.randint(-15, 15))),
                max(0, min(255, FLOOR_COLOR[1] + rng.randint(-5, 5))),
                max(0, min(255, FLOOR_COLOR[2] + rng.randint(-5, 5)))
            )

        castle_map[(x, y, floor)] = (tile_type, floor_color)

    return castle_map[(x, y, floor)]


def get_collectible(x, y, floor):
    if (x, y, floor) in collected_set:
        return None

    # deterministic per-tile seed (original behavior)
    seed = f"{game_seed}-coll-{x},{y},{floor}" if game_seed else f"default-coll-{x},{y},{floor}"
    rng = random.Random(seed)

    # original spawn rate restored
    if rng.random() < 0.05:
        return rng.choice([50, 100, 150])

    return None

    # deterministic per-tile seed
    seed = f"{game_seed}-coll-{x},{y},{floor}" if game_seed else f"default-coll-{x},{y},{floor}"
    rng = random.Random(seed)

    # increased spawn rate so cubes are clearly visible
    if rng.random() < 0.25:
        return rng.choice([50, 100, 150])

    return None

    seed = f"{game_seed}-coll-{x},{y},{floor}" if game_seed else f"default-coll-{x},{y},{floor}"
    rng = random.Random(seed)

    if rng.random() < 0.05:
        return rng.choice([50, 100, 150])
    return None

    seed = f"{game_seed}-coll-{x},{y},{floor}" if game_seed else f"default-coll-{x},{y},{floor}"
    rng = random.Random(seed)

    if rng.random() < 0.05:
        return rng.choice([50, 100, 150])
    return None


# =========================
# DRAW FLOOR
# =========================
def draw_floor(offset_x, offset_y, floor):
    global twist_offset
    twist_offset += 0.02

    start_x = int(offset_x // TILE_SIZE) - 1
    start_y = int(offset_y // TILE_SIZE) - 1
    tiles_w = SCREEN_WIDTH // TILE_SIZE + 3
    tiles_h = SCREEN_HEIGHT // TILE_SIZE + 3

    pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2

    for y in range(start_y, start_y + tiles_h):
        for x in range(start_x, start_x + tiles_w):
            tile_type, floor_color = get_tile(x, y, floor)

            rect_x = x * TILE_SIZE - offset_x + int(math.sin(twist_offset + x * 0.3) * 10)
            rect_y = y * TILE_SIZE - offset_y + int(math.cos(twist_offset + y * 0.3) * 10)
            rect = pygame.Rect(rect_x, rect_y, TILE_SIZE, TILE_SIZE)

            if tile_type == 1:
                pygame.draw.rect(screen, floor_color, rect)
            elif tile_type == 2:
                glow = tuple(min(255, c + int(50 * pulse)) for c in STAIR_COLOR)
                pygame.draw.rect(screen, glow, rect)
            else:
                pygame.draw.rect(screen, floor_color, rect)


# =========================
# MUZAN AI
# =========================
def update_muzan():
    global muzan_x, muzan_y, muzan_floor, floor_changed

    dx = player_x - muzan_x
    dy = player_y - muzan_y
    dist = max(1, math.sqrt(dx * dx + dy * dy))

    muzan_x += player_speed * dx / dist
    muzan_y += player_speed * dy / dist

    # When the player teleports floors, move Muzan to a random castle location
    if floor_changed:
        muzan_floor = player_floor
        rng = random.Random(f"{game_seed}-muzan-tele-{muzan_floor}-{pygame.time.get_ticks()}") if game_seed else random.Random()
        muzan_x = rng.randint(-10, 10) * TILE_SIZE
        muzan_y = rng.randint(-10, 10) * TILE_SIZE
        floor_changed = False


# =========================
# RESET GAME
# =========================
def reset_game():
    global player_x, player_y, player_floor, kimetsu_points
    global muzan_x, muzan_y, muzan_floor, muzan_active
    global collected_set, castle_map, orange_cubes_map
    global game_seed, start_time, final_time, state

    game_seed = random.getrandbits(64)
    player_x = 0
    player_y = 0
    player_floor = 0
    kimetsu_points = 0
    collected_set = set()
    castle_map = {}
    orange_cubes_map = {}

    angle = random.uniform(0, 2 * math.pi)
    distance = random.randint(5, 12) * TILE_SIZE
    muzan_x = int(math.cos(angle) * distance)
    muzan_y = int(math.sin(angle) * distance)
    muzan_floor = 0
    muzan_active = True
    state = "game"


# =========================
# MAIN LOOP
# =========================
def main():
    global player_x, player_y, player_floor, kimetsu_points
    global muzan_active, state, final_time, floor_changed

    clock = pygame.time.Clock()
    state = "intro"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if state == "intro" or state in ["game_over", "muzan_defeated"]:
                        reset_game()

        keys = pygame.key.get_pressed()

        if state == "game":
            dx = dy = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy = -player_speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy = player_speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx = -player_speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx = player_speed

            new_x = player_x + dx
            new_y = player_y + dy
            tile_type, _ = get_tile(new_x // TILE_SIZE, new_y // TILE_SIZE, player_floor)

            if tile_type != 1:
                player_x = new_x
                player_y = new_y

            if tile_type == 2:
                floor_changed = True
                player_floor += 1 if random.random() < 0.5 else -1

            px = round(player_x / TILE_SIZE)
            py = round(player_y / TILE_SIZE)
            val = get_collectible(px, py, player_floor)
            if val:
                kimetsu_points += val
                collected_set.add((px, py, player_floor))

            if muzan_active:
                update_muzan()

            if abs(player_x - muzan_x) < player_size and abs(player_y - muzan_y) < player_size:
                if kimetsu_points >= 12000:
                    state = "muzan_defeated"
                else:
                    state = "game_over"

        offset_x = player_x - SCREEN_WIDTH // 2
        offset_y = player_y - SCREEN_HEIGHT // 2

        screen.fill((30, 0, 30))

        # =========================
        # DRAW STATES
        # =========================
        if state == "intro":
            screen.blit(image, (0, 0))
            draw_text_with_outline("INFINITY CASTLE 2D", super_large_font, RED, WHITE, SCREEN_WIDTH // 2, 80, screen)
            draw_text_with_outline("Press ENTER to play", font, RED, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, screen)

        elif state in ["game", "muzan_defeated"]:
            draw_floor(offset_x, offset_y, player_floor)

            # =========================
            # COLLECTIBLE RENDERING
            # =========================
            for dy in range(-10, 11):
                for dx in range(-10, 11):
                    tx = (player_x // TILE_SIZE) + dx
                    ty = (player_y // TILE_SIZE) + dy
                    val = get_collectible(tx, ty, player_floor)
                    if val:
                        cube_size = player_size // 4
                        screen_x = tx * TILE_SIZE - offset_x
                        screen_y = ty * TILE_SIZE - offset_y
                        pygame.draw.rect(screen, (255, 255, 0), (screen_x, screen_y, cube_size, cube_size))

            screen.blit(player_icon, (player_x - offset_x, player_y - offset_y))

            if muzan_active and muzan_floor == player_floor:
                mx = muzan_x - offset_x
                my = muzan_y - offset_y

                if state == "muzan_defeated":
                    # Split sprite into top and bottom halves
                    w, h = muzan_icon.get_size()

                    top_half = muzan_icon.subsurface((0, 0, w, h // 2))
                    bottom_half = muzan_icon.subsurface((0, h // 2, w, h // 2))

                    # small separation animation
                    split_offset = 15

                    screen.blit(top_half, (mx, my - split_offset))
                    screen.blit(bottom_half, (mx, my + h // 2 + split_offset))
                else:
                    screen.blit(muzan_icon, (mx, my))

                    health_text = f"Health: {muzan_health}"
                    draw_text_with_outline(
                        health_text,
                        small_font,
                        RED,
                        BLACK,
                        mx,
                        my - 25,
                        screen
                    )

            draw_text_with_outline(f"Floor: {player_floor}", font, RED, WHITE, 120, 30, screen)
            draw_text_with_outline(f"Points: {kimetsu_points}", font, RED, WHITE, SCREEN_WIDTH - 150, 30, screen)

        if state == "game_over":
            draw_text_with_outline("YOU DIED", large_font, RED, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, screen)
            draw_text_with_outline("Press ENTER to restart", font, RED, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, screen)

        elif state == "muzan_defeated":
            draw_text_with_outline("YOU BEAT MUZAN!", large_font, RED, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100, screen)
            draw_text_with_outline("Press ENTER to restart", font, RED, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
