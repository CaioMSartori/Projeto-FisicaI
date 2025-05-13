import pygame
import sys
import math
import random

# Inicializa o Pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 800, 600
FPS = 60

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)

# Tela
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rotating Platformer")
clock = pygame.time.Clock()

# Estados do jogo
MENU = 'menu'
DIFFICULTY = 'difficulty'
GAME = 'game'
GAME_OVER = 'game_over'

# Dificuldades
DIFFICULTIES = ['Fácil', 'Médio', 'Difícil']
UNLOCKED = [True, False, False]

# Variáveis do jogo
state = MENU
selected_difficulty = 0

# Jogador
player_radius = 20
player_x = WIDTH // 3
player_y = HEIGHT - 150

# Pulo
jump = False
vy = 0
vx = 0
speed = 5
gravity = 0.5

# Pontuação
score = 0

# Plataforma
platforms = []
platform_distance = 245  # Distância maior entre plataformas para facilitar os pulos

# Plataforma inicial
initial_platform = {'x': 380, 'y': HEIGHT - 100}


def draw_text(text, size, color, x, y):
    font = pygame.font.SysFont(None, size)
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)


def spawn_platform(last_x, last_y):
    x = last_x + platform_distance
    y = last_y + random.randint(-30, 30)  # variação suave
    y = max(300, min(y, HEIGHT - 200))  # garante que as plataformas não fiquem muito abaixo
    radius = random.randint(30, 100)
    return {'x': x, 'y': y, 'angle': 0, 'radius': radius}


def menu():
    global state
    while True:
        screen.fill(WHITE)
        draw_text("Rotating Platformer", 60, BLACK, WIDTH // 2, HEIGHT // 4)
        draw_text("1. Começar", 40, BLACK, WIDTH // 2, HEIGHT // 2)
        draw_text("2. Sair", 40, BLACK, WIDTH // 2, HEIGHT // 2 + 60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    state = DIFFICULTY
                    return
                if event.key == pygame.K_2:
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(FPS)


def difficulty_select():
    global state, selected_difficulty
    while True:
        screen.fill(WHITE)
        draw_text("Selecione a Dificuldade", 50, BLACK, WIDTH // 2, HEIGHT // 4)

        for i, diff in enumerate(DIFFICULTIES):
            color = (0, 200, 0) if UNLOCKED[i] else (180, 180, 180)
            draw_text(f"{i+1}. {diff}", 40, color, WIDTH // 2, HEIGHT // 2 + i * 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    idx = event.key - pygame.K_1
                    if UNLOCKED[idx]:
                        selected_difficulty = idx
                        state = GAME
                        return

        pygame.display.flip()
        clock.tick(FPS)


def game_over():
    global state
    while True:
        screen.fill(WHITE)
        draw_text("Game Over!", 60, RED, WIDTH // 2, HEIGHT // 3)
        draw_text(f"Pontuação: {score}", 40, BLACK, WIDTH // 2, HEIGHT // 2)
        draw_text("Pressione Enter para voltar ao menu", 30, BLACK, WIDTH // 2, HEIGHT // 2 + 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    state = MENU
                    return

        pygame.display.flip()
        clock.tick(FPS)


def game_loop():
    global player_x, player_y, vy, vx, jump, score, platforms, state

    # Reset
    player_x = WIDTH // 3 + 150
    player_y = initial_platform['y'] - player_radius
    vy = 0
    vx = 0
    jump = False
    score = 0
    platforms = []

    # Cria primeiras plataformas
    last_x = initial_platform['x'] + 25  # primeira roda após a plataforma inicial
    last_y = initial_platform['y']
    for _ in range(10):
        platforms.append(spawn_platform(last_x, last_y))
        last_x = platforms[-1]['x']
        last_y = platforms[-1]['y']

    # Variável para controlar a plataforma na qual o jogador está
    last_landed_platform = None

    while True:
        screen.fill(WHITE)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not jump:
            vy = -12  # Ajuste a força do pulo aqui
            vx = speed

        # Atualiza jogador
        player_y += vy
        player_x += vx
        vy += gravity
        jump = True

        # Game Over se cair
        if player_y > HEIGHT:
            state = GAME_OVER
            return

        # Plataforma inicial (reta e fixa)
        px = initial_platform['x'] - (player_x - WIDTH // 3)
        py = initial_platform['y']
        pygame.draw.rect(screen, GRAY, (px - 100, py, 200, 10))

        # Colisão com plataforma inicial
        if (px - 100) < WIDTH // 3 < (px + 100) and player_y + player_radius > py and vy > 0:
            player_y = py - player_radius
            vy = 0
            vx = 0
            jump = False

        # Atualiza e desenha plataformas giratórias
        for p in platforms:
            p['angle'] += 0.03
            px = p['x'] - (player_x - WIDTH // 3)
            py = p['y']
            radius = p['radius']

            # Base da plataforma giratória
            pygame.draw.circle(screen, GRAY, (int(px), int(py)), radius, 5)

            # Suportes fixos na plataforma
            for i in range(4):
                angle = p['angle'] + math.radians(90 * i)
                sx = px + math.cos(angle) * radius
                sy = py + math.sin(angle) * radius
                pygame.draw.rect(screen, BLUE, (sx - 20, sy - 5, 40, 10))  # Suportes horizontais

                # Colisão
                dist = math.hypot(WIDTH // 3 - sx, player_y - sy)
                if dist < player_radius + 10 and vy > 0:
                    player_y = sy - player_radius
                    vy = 0
                    vx = 0
                    jump = False

                    # Movimento horizontal induzido pela rotação
                    # Derivada de x em relação ao tempo na circunferência: dx = -sen(θ) * ω * r
                    dx = -math.sin(angle) * 0.03 * radius
                    player_x += dx  # Aplica esse movimento ao jogador

                    if last_landed_platform != p:
                        score += 1
                        last_landed_platform = p


        # Remove plataformas fora da tela
        if platforms and platforms[0]['x'] - (player_x - WIDTH // 3) < -100:
            platforms.pop(0)

        # Spawna novas
        if platforms and platforms[-1]['x'] < player_x + WIDTH:
            last_x = platforms[-1]['x']
            last_y = platforms[-1]['y']
            platforms.append(spawn_platform(last_x, last_y))

        # Jogador
        pygame.draw.circle(screen, RED, (WIDTH // 3, int(player_y)), player_radius)

        # Pontuação
        draw_text(f"Pontos: {score}", 30, BLACK, WIDTH // 2, 30)

        pygame.display.flip()
        clock.tick(FPS)


# Loop principal
while True:
    if state == MENU:
        menu()
    elif state == DIFFICULTY:
        difficulty_select()
    elif state == GAME:
        game_loop()
    elif state == GAME_OVER:
        game_over()