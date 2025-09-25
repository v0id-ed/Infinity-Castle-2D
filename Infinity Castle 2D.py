import pygame
import sys
import random
import math

pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
RED = (200, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Tile and player settings
TILE_SIZE = 64
player_size = 32
player_speed = 5

# Colors
FLOOR_COLOR = (139, 0, 0)      # dark red base
STAIR_COLOR = (255, 69, 0)     # orangish red
WALL_BROWNS = [(139, 69, 19), (160, 82, 45), (101, 67, 33)]  # limited shades

# Load player and enemy icons
player_icon = pygame.image.load("Tanjiro.jpg")
player_icon = pygame.transform.smoothscale(player_icon, (player_size, player_size))
muzan_icon = pygame.image.load("Muzan.jpg")
muzan_icon = pygame.transform.smoothscale(muzan_icon, (player_size, player_size))

# Intro image
image = pygame.image.load("Infinity Castle.png")
img_width, img_height = image.get_size()
scale = max(SCREEN_WIDTH / img_width, SCREEN_HEIGHT / img_height)
new_size = (int(img_width * scale), int(img_height * scale))
scaled_image = pygame.transform.smoothscale(image, new_size)
img_x = (new_size[0] - SCREEN_WIDTH) // 2
img_y = (new_size[1] - SCREEN_HEIGHT) // 2
image = scaled_image.subsurface((img_x, img_y, SCREEN_WIDTH, SCREEN_HEIGHT)).copy()

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Infinity Castle 2D")
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 48)

# Player and game state
player_x = 0
player_y = 0
player_floor = 0
kimetsu_points = 0

# Stair portal tracking
stair_portal_x = None
stair_portal_y = None
floor_changed = False

# Muzan state
muzan_x = 0
muzan_y = 0
muzan_floor = 0
muzan_health = 12000
muzan_active = False

# Maps
castle_map = {}
orange_cubes_map = {}
twist_offset = 0

# Keep track of collected tiles
collected_set = set()

# Stopwatch
start_time = None
final_time = None  # freezes when win/lose

def get_tile(x, y, floor):
    if (x, y, floor) not in castle_map:
        r = random.random()
        if r < 0.1:
            tile_type = 1  # Wall
            floor_color = random.choice(WALL_BROWNS)
        elif r < 0.12:
            tile_type = 2  # Stair
            floor_color = None
        else:
            tile_type = 0  # Floor
            r_shift = random.randint(-15, 15)
            g_shift = random.randint(-5, 5)
            b_shift = random.randint(-5, 5)
            floor_color = (
                max(0, min(255, FLOOR_COLOR[0]+r_shift)),
                max(0, min(255, FLOOR_COLOR[1]+g_shift)),
                max(0, min(255, FLOOR_COLOR[2]+b_shift))
            )
        castle_map[(x, y, floor)] = (tile_type, floor_color)
    return castle_map[(x, y, floor)]

def get_collectible(x, y, floor):
    if (x, y, floor) in collected_set:
        return None
    seed_str = f"{x},{y},{floor}"
    random.seed(seed_str)
    if random.random() < 0.05:  # 5% chance of collectible
        return random.choice([50, 100, 150])
    return None

def draw_text_with_outline(text, font, text_color, outline_color, x, y, screen):
    text_surface = font.render(text, True, text_color)
    outline = font.render(text, True, outline_color)
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx!=0 or dy!=0:
                screen.blit(outline,(x+dx,y+dy))
    screen.blit(text_surface,(x,y))

def draw_floor(offset_x, offset_y, floor):
    global twist_offset
    twist_offset += 0.02
    start_x = int(offset_x // TILE_SIZE)-1
    start_y = int(offset_y // TILE_SIZE)-1
    tiles_w = SCREEN_WIDTH // TILE_SIZE + 3
    tiles_h = SCREEN_HEIGHT // TILE_SIZE + 3
    time_ms = pygame.time.get_ticks()
    pulse = (math.sin(time_ms * 0.005) + 1)/2  # 0 to 1

    for y in range(start_y, start_y+tiles_h):
        for x in range(start_x, start_x+tiles_w):
            tile_type, floor_color = get_tile(x, y, floor)
            rect_x = x*TILE_SIZE - offset_x + int(math.sin(twist_offset + x*0.3)*10)
            rect_y = y*TILE_SIZE - offset_y + int(math.cos(twist_offset + y*0.3)*10)
            rect = pygame.Rect(rect_x, rect_y, TILE_SIZE, TILE_SIZE)

            if tile_type == 1:
                pygame.draw.rect(screen, floor_color, rect)
                if (x, y, floor) not in orange_cubes_map:
                    orange_cubes_map[(x, y, floor)] = random.random() < 0.1
                if orange_cubes_map[(x, y, floor)]:
                    cube_size = TILE_SIZE//4
                    cube_x = rect_x + TILE_SIZE//2 - cube_size//2
                    cube_y = rect_y + TILE_SIZE//2 - cube_size//2
                    color = (255, 165, int(165 * pulse))
                    pygame.draw.rect(screen, color, (cube_x, cube_y, cube_size, cube_size))
            elif tile_type == 2:
                pulsing_color = tuple(min(255, c + int(50*pulse)) for c in STAIR_COLOR)
                pygame.draw.rect(screen, pulsing_color, rect)
            else:
                pygame.draw.rect(screen, floor_color, rect)

def update_muzan():
    global muzan_x, muzan_y, muzan_floor, floor_changed
    dx = player_x - muzan_x
    dy = player_y - muzan_y
    dist = max(1,(dx**2+dy**2)**0.5)
    muzan_x += player_speed*dx/dist
    muzan_y += player_speed*dy/dist

    if floor_changed:
        muzan_floor = player_floor
        muzan_x = random.randint(-10,10)*TILE_SIZE
        muzan_y = random.randint(-10,10)*TILE_SIZE
        floor_changed = False

def reset_game():
    global player_x, player_y, player_floor, kimetsu_points, muzan_x, muzan_y, muzan_floor, muzan_active, state
    global stair_portal_x, stair_portal_y, floor_changed, collected_set, start_time, final_time
    player_x = 0
    player_y = 0
    player_floor = 0
    kimetsu_points = 0
    collected_set = set()

    muzan_floor = 0
    angle = random.uniform(0, 2*math.pi)
    distance = random.randint(5, 12)*TILE_SIZE
    muzan_x = player_x + int(math.cos(angle)*distance)
    muzan_y = player_y + int(math.sin(angle)*distance)
    muzan_active = True

    stair_portal_x = stair_portal_y = None
    floor_changed = False
    state = "game"

    # start stopwatch
    start_time = pygame.time.get_ticks()
    final_time = None

def main():
    global player_x, player_y, player_floor, kimetsu_points, muzan_active, state
    global stair_portal_x, stair_portal_y, floor_changed, collected_set, start_time, final_time
    clock = pygame.time.Clock()
    state = "intro"
    offset_x = offset_y = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False
            elif event.type == pygame.KEYDOWN:
                if state=="intro" and event.key==pygame.K_RETURN:
                    reset_game()
                elif state in ["game_over","muzan_defeated"] and event.key==pygame.K_RETURN:
                    state="intro"

        keys = pygame.key.get_pressed()
        if state=="game":
            dx = dy = 0
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy=-player_speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy=player_speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx=-player_speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx=player_speed
            new_x = player_x+dx
            new_y = player_y+dy
            tile_type,_ = get_tile(new_x//TILE_SIZE,new_y//TILE_SIZE,player_floor)
            if tile_type!=1:
                player_x=new_x
                player_y=new_y
            if tile_type==2:
                stair_portal_x = player_x
                stair_portal_y = player_y
                new_floor = player_floor + (1 if random.random()<0.5 else -1)
                if new_floor != player_floor:
                    floor_changed = True
                    player_floor = new_floor
                    player_x = stair_portal_x + TILE_SIZE
                    player_y = stair_portal_y

            # Check for collectible pickup
            px = round(player_x / TILE_SIZE)
            py = round(player_y / TILE_SIZE)
            val = get_collectible(px, py, player_floor)
            if val:
                kimetsu_points += val
                collected_set.add((px, py, player_floor))

            if not muzan_active and random.random()<0.005:
                muzan_active=True
            if muzan_active:
                update_muzan()

            if muzan_active and muzan_floor==player_floor and abs(player_x-muzan_x)<player_size and abs(player_y-muzan_y)<player_size:
                if kimetsu_points < 150:
                    state = "game_over"
                    final_time = (pygame.time.get_ticks() - start_time)//1000
                else:
                    state = "muzan_defeated"
                    muzan_active = False
                    final_time = (pygame.time.get_ticks() - start_time)//1000

            offset_x=player_x-SCREEN_WIDTH//2
            offset_y=player_y-SCREEN_HEIGHT//2

        # Draw
        screen.fill(BLACK if state=="game_over" else (30,0,30))
        if state=="intro":
            screen.blit(image,(0,0))
            draw_text_with_outline("INFINITY CASTLE 2D", large_font, RED, WHITE, SCREEN_WIDTH//2-large_font.size("INFINITY CASTLE 2D")[0]//2, 50, screen)
            draw_text_with_outline("Press ENTER to play", font, RED, WHITE, SCREEN_WIDTH//2-font.size("Press ENTER to play")[0]//2, SCREEN_HEIGHT-100, screen)
        elif state=="game" or state=="muzan_defeated":
            draw_floor(offset_x, offset_y, player_floor)

            # Draw collectibles procedurally around player
            for dy in range(-10, 11):
                for dx in range(-10, 11):
                    tx = (player_x // TILE_SIZE) + dx
                    ty = (player_y // TILE_SIZE) + dy
                    val = get_collectible(tx, ty, player_floor)
                    if val:
                        cube_size = player_size // 4
                        screen_x = tx*TILE_SIZE - offset_x
                        screen_y = ty*TILE_SIZE - offset_y
                        pygame.draw.rect(screen, (255, 255, 0), (screen_x, screen_y, cube_size, cube_size))

            screen.blit(player_icon,(player_x-offset_x,player_y-offset_y))
            if muzan_active and muzan_floor==player_floor:
                screen.blit(muzan_icon,(muzan_x-offset_x,muzan_y-offset_y))
                health_text = f"Health: {muzan_health}"
                text_width = font.size(health_text)[0]
                draw_text_with_outline(health_text, font, RED, BLACK, muzan_x - offset_x - text_width//2, muzan_y - offset_y - 25, screen)

            draw_text_with_outline(f"Floor: {player_floor}", font, RED, WHITE, 10,10,screen)
            draw_text_with_outline("Kimetsu Points:", font, RED, WHITE, SCREEN_WIDTH-240, 10, screen)
            draw_text_with_outline(str(kimetsu_points), font, RED, WHITE, SCREEN_WIDTH-240, 10+font.get_height(), screen)

            # Stopwatch
            if state == "game":
                elapsed = (pygame.time.get_ticks() - start_time)//1000
            else:
                elapsed = final_time if final_time is not None else 0
            timer_text = f"Time: {elapsed}s"
            draw_text_with_outline(timer_text, font, RED, WHITE, SCREEN_WIDTH//2 - font.size(timer_text)[0]//2, 10, screen)

            # Rank S if <=10s
            if state == "muzan_defeated" and final_time is not None and final_time <= 10:
                rank_text = "Rank: S"
                draw_text_with_outline(rank_text, large_font, RED, WHITE, SCREEN_WIDTH//2 - large_font.size(rank_text)[0]//2, 50, screen)

            fog=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
            fog.fill((0,0,0,50))
            screen.blit(fog,(0,0))

        if state=="game_over":
            draw_text_with_outline("You Died", large_font, RED, WHITE, SCREEN_WIDTH//2-large_font.size("You Died")[0]//2, SCREEN_HEIGHT//2-50, screen)
            draw_text_with_outline("Press ENTER to restart", font, RED, WHITE, SCREEN_WIDTH//2-font.size("Press ENTER to restart")[0]//2, SCREEN_HEIGHT-100, screen)
        elif state=="muzan_defeated":
            top_half = muzan_icon.subsurface((0,0,player_size,player_size//2))
            bottom_half = muzan_icon.subsurface((0,player_size//2,player_size,player_size//2))
            screen.blit(top_half,(SCREEN_WIDTH//2-player_size//2, SCREEN_HEIGHT//2-player_size))
            screen.blit(bottom_half,(SCREEN_WIDTH//2-player_size//2, SCREEN_HEIGHT//2))
            draw_text_with_outline("You Beat Muzan!", large_font, RED, WHITE, SCREEN_WIDTH//2-large_font.size("You Beat Muzan!")[0]//2, SCREEN_HEIGHT//2-100, screen)
            draw_text_with_outline("Press ENTER to restart", font, RED, WHITE, SCREEN_WIDTH//2-font.size("Press ENTER to restart")[0]//2, SCREEN_HEIGHT-100, screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__=="__main__":
    main()
