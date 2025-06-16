import pygame
import sys
import os
import json
import math
import random

# Inicializa o Pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 800, 600
FPS = 60
FPS_BG = 30

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)

# Tela
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Just Jump!")
clock = pygame.time.Clock()

def load_background_frames(folder_path):
    frames = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            path = os.path.join(folder_path, filename)
            image = pygame.image.load(path).convert()
            image = pygame.transform.scale(image, (WIDTH, HEIGHT))  # Ajusta ao tamanho da tela
            frames.append(image)
    return frames

base_path = os.path.dirname(__file__)
background_folder = os.path.join(base_path, "background")
gameover_sprite = os.path.join(base_path, "gameover.png")
title_sprite = os.path.join(base_path, "title.png")
face_sprite = os.path.join(base_path, "face.png")

gameover = pygame.transform.rotozoom(pygame.image.load(gameover_sprite).convert_alpha(), 0, 1.5)
gameover_rect = gameover.get_rect(center=(WIDTH // 2, HEIGHT // 3))

title = pygame.image.load(title_sprite).convert_alpha()
title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))

face = pygame.transform.scale(pygame.image.load(face_sprite).convert_alpha(), (40, 40))

background_frames = load_background_frames(background_folder)
frame_index = 0
frame_count = 0

# Estados do jogo
MENU = 'menu'
DIFFICULTY = 'difficulty'
GAME = 'game'
GAME_OVER = 'game_over'

# Dificuldades
DIFFICULTIES = ['Fácil', 'Médio', 'Difícil']

DIFFICULTY_PARAMS = {
    0: {  # Fácil
        "rotation_speed_range": (0.01, 0.02),
        "laser_active": False,
        "timer_active": False,
        "laser_interval": 0,
    },
    1: {  # Médio
        "rotation_speed_range": (0.02, 0.03),
        "laser_active": True,
        "timer_active": False,
        "laser_interval": 3000,
    },
    2: {  # Difícil
        "rotation_speed_range": (0.02, 0.04),
        "laser_active": True,
        "timer_active": True,
        "laser_interval": 2000,
    }
}

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

# Pontuação e funções para manipular o recorde
score = 0

high_score_path = os.path.join(base_path, "recordes.json")
def load_high_scores():
    if os.path.exists(high_score_path):
        with open(high_score_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {str(i): 0 for i in range(3)}
    return {str(i): 0 for i in range(3)}

def save_high_scores(high_scores):
    with open(high_score_path, "w") as f:
        json.dump(high_scores, f)

high_scores = load_high_scores()

# Plataforma
platforms = []
platform_distance = 245  # Distância maior entre plataformas para facilitar os pulos

# Plataforma inicial
initial_platform = {'x': 380, 'y': HEIGHT - 100}

# Timer para o contador de 5 segundos
platform_timer = 0  # Variável para armazenar o tempo de aterrissagem

def draw_text(text, size, color, x, y):
    font = pygame.font.SysFont(None, size)
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)

def spawn_platform(last_x, last_y, difficulty):
    x = last_x + platform_distance
    y = last_y + random.randint(-30, 30)  # variação suave
    y = max(300, min(y, HEIGHT - 200))  # garante que as plataformas não fiquem muito abaixo
    radius = random.randint(30, 100)
    
    # Determina o número de suportes com base no raio
    if 30 <= radius <= 50:
        rect_number = random.randint(1, 2)
    elif 51 <= radius <= 70:
        rect_number = random.randint(3, 4)
    else:
        rect_number = random.randint(4, 6)

    # Define uma velocidade de rotação aleatória para cada plataforma
    rotation_speed_range = DIFFICULTY_PARAMS[difficulty]["rotation_speed_range"]
    rotation_speed = random.uniform(*rotation_speed_range)

    # Determina a direção de rotação aleatória: 1 para horário, -1 para anti-horário
    rotation_direction = random.choice([1, -1]) 

    return {'x': x, 'y': y, 'angle': 0, 'radius': radius, 'number': rect_number, 
            'rotation_speed': rotation_speed, 'rotation_direction': rotation_direction}

def spawn_laser_between(p1, p2, difficulty):
    if not DIFFICULTY_PARAMS[difficulty]["laser_active"]:
        return None  # Não cria laser se a dificuldade não permitir
    
    x = (p1['x'] + p2['x']) // 2
    y1_top = p1['y'] - p1['radius']
    y2_top = p2['y'] - p2['radius']
    y = min(y1_top, y2_top) - 250  # posiciona acima das plataformas
    return {'x': x, 'y': y, 'last_fire': pygame.time.get_ticks(), 'beam_active': False}

def menu():
    global state
    while True:
        screen.fill(BLACK)
        screen.blit(title, title_rect)

        draw_text("1. Começar", 40, WHITE, WIDTH // 2, HEIGHT // 2)
        draw_text("2. Sair", 40, WHITE, WIDTH // 2, HEIGHT // 2 + 60)

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
        screen.fill(BLACK)
        draw_text("Selecione a Dificuldade", 50, WHITE, WIDTH // 2, HEIGHT // 4)

        # Cores por dificuldade
        difficulty_colors = [(0, 200, 0), (255, 140, 0), (200, 0, 0)]

        # Exibe as três dificuldades
        for i, diff in enumerate(DIFFICULTIES):
            color = difficulty_colors[i]
            draw_text(f"{i+1}. {diff}", 40, color, WIDTH // 2, HEIGHT // 2 + i * 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    idx = event.key - pygame.K_1
                    selected_difficulty = idx
                    state = GAME
                    return

        pygame.display.flip()
        clock.tick(FPS)

def game_over():
    global state
    while True:
        screen.fill(BLACK)
        screen.blit(gameover, gameover_rect)

        draw_text(f"Pontuação: {score}", 40, WHITE, WIDTH // 2, HEIGHT // 2)
        draw_text(f"Recorde: {high_scores[str(selected_difficulty)]}", 35, WHITE, WIDTH // 2, HEIGHT // 2 + 50)
        draw_text("Pressione Enter para voltar ao menu", 30, WHITE, WIDTH // 2, HEIGHT // 2 + 100)

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
    global player_x, player_y, vy, vx, jump, score, platforms, state, platform_timer, high_score, frame_index, frame_count

    # Reset
    player_x = WIDTH // 3 + 150
    player_y = initial_platform['y'] - player_radius
    face_rect = face.get_rect(center=(player_x, player_y))
    vy = 0
    vx = 0
    jump = False
    score = 0
    platforms = []
    lasers = []
    laser_cooldown = DIFFICULTY_PARAMS[selected_difficulty]["laser_interval"]

    # Reinicia o temporizador (para o contador de 5 segundos)
    platform_timer = pygame.time.get_ticks()  # Reinicia o tempo ao começar o jogo

    # Cria primeiras plataformas
    last_x = initial_platform['x'] + 25  # primeira roda após a plataforma inicial
    last_y = initial_platform['y']
    platform_passed_count = 0
    for _ in range(10):
        platforms.append(spawn_platform(last_x, last_y, selected_difficulty))
        last_x = platforms[-1]['x']
        last_y = platforms[-1]['y']

        # A cada 4 plataformas passadas, cria um laser
        platform_passed_count += 1
        if platform_passed_count % 4 == 0:
            # Cria o laser entre a última plataforma e a anterior
            if len(platforms) >= 2:
                p1 = platforms[-2]  # Plataforma anterior à última
                p2 = platforms[-1]  # Última plataforma
                laser = spawn_laser_between(p1, p2, selected_difficulty)
                if laser:
                    lasers.append(laser)

    # Variável para controlar a plataforma na qual o jogador está
    last_landed_platform = None

    while True:
        frame_count += 1

        if frame_count % (FPS // FPS_BG) == 0:
            frame_index = (frame_index + 1) % len(background_frames)
        screen.blit(background_frames[frame_index], (0, 0))
        
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
            platform_timer = pygame.time.get_ticks()  # Reinicia o tempo ao pular

        # Atualiza jogador
        player_y += vy
        player_x += vx
        vy += gravity
        jump = True

        # Game Over se cair
        if player_y > HEIGHT:
            if score > high_scores[str(selected_difficulty)]:
                high_scores[str(selected_difficulty)] = score
                save_high_scores(high_scores)
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
            p['angle'] += p['rotation_speed'] * p['rotation_direction'] # Usa a velocidade de rotação randomizada e em sentidos opostos
            px = p['x'] - (player_x - WIDTH // 3)
            py = p['y']
            radius = p['radius']

            # Base da plataforma giratória
            pygame.draw.circle(screen, GRAY, (int(px), int(py)), radius, 5)

            # Suportes fixos na plataforma
            for i in range(p['number']):
                angle = p['angle'] + math.radians(360/p['number'] * i)
                sx = px + math.cos(angle) * radius
                sy = py + math.sin(angle) * radius
                pygame.draw.rect(screen, CYAN, (sx - 20, sy - 5, 40, 10))  # Suportes horizontais

                # Colisão
                dist = math.hypot(WIDTH // 3 - sx, player_y - sy)
                if dist < player_radius + 10 and vy > 0:
                    player_y = sy - player_radius
                    vy = 0
                    vx = 0
                    jump = False
                    
                    # Movimento horizontal induzido pela rotação
                    # Derivada de x em relação ao tempo na circunferência: dx = -sen(θ) * ω * r
                    dx = -math.sin(angle) * p['rotation_speed'] * p['rotation_direction'] * radius
                    player_x += dx  # Aplica esse movimento ao jogador

                    # Incrementa a pontuação apenas quando o jogador aterrissar em uma plataforma nova
                    if last_landed_platform != p:
                        score += 1
                        last_landed_platform = p  # Atualiza a plataforma onde o jogador aterrissou

        # Verifica se o tempo parado excedeu 5 segundos
        if DIFFICULTY_PARAMS[selected_difficulty]["timer_active"]:
            elapsed = pygame.time.get_ticks() - platform_timer
            if elapsed > 5000:  # 5 segundos em milissegundos
                if score > high_scores[str(selected_difficulty)]:
                    high_scores[str(selected_difficulty)] = score
                    save_high_scores(high_scores)
                state = GAME_OVER
                return

            # Temporizador visual
            remaining = max(0, 5 - elapsed // 1000)
            draw_text(f"Tempo para pular: {remaining}", 25, RED, WIDTH // 2, 60)

        # Remove plataformas fora da tela
        if platforms and platforms[0]['x'] - (player_x - WIDTH // 3) < -100:
            platforms.pop(0)

        # Spawna novas
        if platforms and platforms[-1]['x'] < player_x + WIDTH:
            last_x = platforms[-1]['x']
            last_y = platforms[-1]['y']
            platforms.append(spawn_platform(last_x, last_y, selected_difficulty))

        # Jogador
        pygame.draw.circle(screen, (233, 30, 99), (WIDTH // 3, int(player_y)), player_radius)
        pygame.draw.circle(screen, (186, 85, 211), (WIDTH // 3, int(player_y)), player_radius, 1)

        screen.blit(face, (WIDTH // 3 - 20, player_y - 20))

        # Olhos do jogador
        # eye_offset_x = 6
        # eye_offset_y = -5
        # pygame.draw.circle(screen, WHITE, (WIDTH // 3 - eye_offset_x, int(player_y) + eye_offset_y), 4)
        # pygame.draw.circle(screen, WHITE, (WIDTH // 3 + eye_offset_x, int(player_y) + eye_offset_y), 4)

        # pygame.draw.circle(screen, BLACK, (WIDTH // 3 - eye_offset_x, int(player_y) + eye_offset_y), 2)
        # pygame.draw.circle(screen, BLACK, (WIDTH // 3 + eye_offset_x, int(player_y) + eye_offset_y), 2)

        # Boca do jogador
        # cx, cy = WIDTH // 3, int(player_y) + 6 
        # pygame.draw.lines(screen, BLACK, False, [
            # (cx - 8, cy + 2),
            # (cx - 4, cy + 3),
            # (cx,     cy + 4),
            # (cx + 4, cy + 3),
            # (cx + 8, cy + 2)
        # ], 2)

        # Pontuação
        draw_text(f"Pontos: {score}", 30, WHITE, WIDTH // 2, 30)
        draw_text(f"Recorde: {high_scores[str(selected_difficulty)]}", 25, CYAN, WIDTH // 2, 90)

        for laser in lasers:
            lx = laser['x'] - (player_x - WIDTH // 3) 
            ly = laser['y']

            # Desenha o emissor
            pygame.draw.rect(screen, GRAY, (lx - 10, ly, 20, 30))

            # Tempo atual
            now = pygame.time.get_ticks()

            # Dispara laser se passou o cooldown
            if now - laser['last_fire'] >= laser_cooldown:
                laser['last_fire'] = now
                laser['beam_active'] = True
                laser['beam_start'] = now

            # Desenha raio enquanto ativo (0.8s)
            if laser.get('beam_active'):
                if now - laser['beam_start'] <= 800:
                    pygame.draw.line(screen, (57, 255, 20), (lx, ly + 30), (lx, HEIGHT), 4)

                    # Colisão com jogador
                    if WIDTH // 3 - player_radius < lx < WIDTH // 3 + player_radius and player_y > ly:
                        if score > high_scores[str(selected_difficulty)]:
                            high_scores[str(selected_difficulty)] = score
                            save_high_scores(high_scores)
                        state = GAME_OVER
                        return
                else:
                    laser['beam_active'] = False
        
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