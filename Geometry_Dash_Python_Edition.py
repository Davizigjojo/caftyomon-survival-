import pygame
import random
import os
import sys

# --- ADAPTAÇÃO PARA PYGAME-WEB/PYSCRIPT ---
# Importa o módulo sys para detectar o ambiente e as funções JS
if 'pyodide' in sys.modules:
    from js import console
    def print_log(*args):
        console.log(*args)
else:
    def print_log(*args):
        print(*args)
# --- FIM DA ADAPTAÇÃO ---

pygame.init()
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

DEBUG_HITBOX = False

GROUND_Y = HEIGHT - 80        
PLAYER_Y_ON_GROUND = GROUND_Y - 16 

# REMOVIDO: BASE_PATH não é mais necessário, PyScript carrega os arquivos
# diretamente pelo nome (ex: "jump.wav") na mesma pasta.

# Inicializa o mixer (áudio)
try:
    pygame.mixer.init()
except Exception as mixer_err:
    print_log("Erro ao iniciar o mixer:", mixer_err) # Alterado para print_log

def load_sound(filename):
    # O caminho é apenas o nome do arquivo
    try:
        return pygame.mixer.Sound(filename)
    except Exception as e:
        print_log(f"Erro ao carregar '{filename}': {e}")
        return None

def load_music(filename):
    # O caminho é apenas o nome do arquivo
    try:
        pygame.mixer.music.load(filename)
        return True
    except Exception as e:
        print_log(f"Erro ao carregar música '{filename}': {e}")
        return False

jump_sound = load_sound("jump.wav")
death_sound = load_sound("death.wav")

def start_music():
    if load_music("music.wav"): # Corrigido para music.wav (o arquivo enviado)
        pygame.mixer.music.play(-1)
    else:
        print_log("Coloque um 'music.wav' na pasta correta!") # Alterado para print_log e .wav

# Inicia música só uma vez!
start_music()

# REMOVIDO: find_sprite_name (dependia de os.path.isfile)
# Carregamento de sprites DIRETO, usando os nomes de arquivo que você enviou:

def load_image(name, size=None):
    try:
        # O caminho é apenas o nome do arquivo
        img = pygame.image.load(name).convert_alpha()
        if size:
            # Usando transform.scale em vez de smoothscale (mais seguro no Pygame-Web)
            img = pygame.transform.scale(img, size) 
        return img
    except Exception as img_err:
        print_log(f"Erro ao carregar imagem '{name}':", img_err)
        return None

# Carregamento direto usando os nomes dos arquivos PNG que você enviou
cube_img = load_image("player.png", (32, 32))
spike_img = load_image("spike.png", (32, 32))
mini_img = load_image("mini-spike.png", (32, 16))

# --- ADAPTAÇÃO: SALVAMENTO DE RECORDE (LOCALSTORAGE) ---
# O recorde agora será salvo diretamente no navegador do jogador.
def save_high_score(score):
    if 'pyodide' in sys.modules:
        try:
            from js import localStorage
            localStorage.setItem("gd_highscore", str(score))
        except:
            print_log("Erro ao salvar recorde no localStorage.")
    else:
        # Lógica de arquivo para desktop (fallback, se rodar fora do navegador)
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(score))
        except:
            pass

def load_high_score():
    if 'pyodide' in sys.modules:
        try:
            from js import localStorage
            score_str = localStorage.getItem("gd_highscore")
            return int(score_str) if score_str else 0
        except:
            return 0
    else:
        # Lógica de arquivo para desktop (fallback)
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0
# --- FIM DA ADAPTAÇÃO: SALVAMENTO DE RECORDE ---

class Player:
    def __init__(self):
        self.x = 120
        self.y = PLAYER_Y_ON_GROUND 
        self.vel_y = 0
        self.on_ground = True
        self.rot = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = -12
            self.on_ground = False
            if jump_sound: jump_sound.play()

    def update(self):
        self.vel_y += 0.6
        self.y += self.vel_y

        if self.y >= PLAYER_Y_ON_GROUND:
            self.y = PLAYER_Y_ON_GROUND
            self.vel_y = 0
            self.on_ground = True

        if not self.on_ground:
            self.rot -= 12
        else:
            self.rot = 0

    def hitbox(self):
        return pygame.Rect(self.x - 15, self.y - 15, 30, 30)

    def draw(self):
        if cube_img:
            img = pygame.transform.rotate(cube_img, self.rot)
            r = img.get_rect(center=(self.x, self.y))
            screen.blit(img, r)
        else:
            pygame.draw.rect(screen, (0, 200, 255), self.hitbox())
        if DEBUG_HITBOX:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox(), 1)

class Spike:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - 32 

    def update(self, s):
        self.x -= s

    def draw(self):
        if spike_img:
            screen.blit(spike_img, (self.x, self.y))
        else:
            pygame.draw.polygon(screen, (255, 50, 50),
                [(self.x, self.y + 32),
                 (self.x + 16, self.y),
                 (self.x + 32, self.y + 32)])
        if DEBUG_HITBOX:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox(), 1)

    def hitbox(self):
        return pygame.Rect(self.x + 8, self.y + 8, 16, 24)

class MiniSpike(Spike):
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - 16 

    def draw(self):
        if mini_img:
            screen.blit(mini_img, (self.x, self.y))
        else:
            pygame.draw.polygon(screen, (200, 50, 50),
                [(self.x, self.y + 16),
                 (self.x + 16, self.y),
                 (self.x + 32, self.y + 16)])
        if DEBUG_HITBOX:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox(), 1)

    def hitbox(self):
        return pygame.Rect(self.x + 10, self.y + 4, 12, 12)

def spawn_group(obs):
    t = random.randint(1, 6)
    if t <= 3:
        obs.append(Spike(WIDTH + 50))
    elif t == 4:
        base = WIDTH + 50
        obs.append(Spike(base))
        obs.append(Spike(base + 32))
    elif t == 5:
        base = WIDTH + 50
        obs.append(Spike(base))
        obs.append(Spike(base + 32))
        obs.append(Spike(base + 64))
    else:
        obs.append(MiniSpike(WIDTH + 50))

def reset(player, obs):
    player.y = PLAYER_Y_ON_GROUND 
    player.vel_y = 0
    player.rot = 0
    obs.clear()
    return 0 

def draw_game_over(score, high_score):
    title = font.render("GAME OVER", True, (255, 50, 50))
    score_text = font.render(f"SCORE: {score}", True, (255, 255, 255))
    high_score_text = font.render(f"RECORD: {high_score}", True, (255, 255, 0))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 60))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 50))

def draw_score(score, high_score):
    score_text = font.render(str(score), True, (255, 255, 255))
    record_text = font.render(f"REC: {high_score}", True, (255,255,0))
    screen.blit(score_text, (20, 20))
    screen.blit(record_text, (20, 55))

font = pygame.font.SysFont("Arial", 38)

def menu(high_score):
    while True:
        screen.fill((30, 30, 30))

        title = font.render("Geometry Dash Python Edition", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        record_txt = font.render(f"Recorde: {high_score}", True, (255, 255, 0))
        screen.blit(record_txt, (WIDTH // 2 - record_txt.get_width() // 2, 110))

        subtitle = font.render("Toque ou tecla para começar", True, (200, 200, 50))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 180))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return False
            # Verifica eventos de toque (MOUSEBUTTONDOWN) ou teclado
            if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP)):
                return True
            # Permite fechar a janela do navegador
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit()
                return False

def pause():
    paused = True
    while paused:
        txt = font.render("[PAUSA] - Pressione 'P' para voltar", True, (255, 200, 50))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                # Não precisa de exit(), apenas retorna para o navegador
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                paused = False

high_score = load_high_score()
player = Player()
obstacles = []
spawn_timer = 0
score = 0
speed = 5 
dead = False
paused = False

# Chamada do menu
if not menu(high_score):
    pygame.quit()
    # Não usa exit() para evitar travamentos no navegador
    sys.exit(0) # Permite que o PyScript encerre

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP)):
            if not dead:
                player.jump()
            else:
                score = reset(player, obstacles)
                dead = False
                start_music()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
            pause()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)

    cor_base = 60 + (score*3 % 120)
    screen.fill((cor_base, 60, 80))
    pygame.draw.rect(screen, (40, 40, 40), (0, GROUND_Y, WIDTH, 80))

    if not dead:
        player.update()
        speed = 5 + score // 10
        spawn_timer += 1
        if spawn_timer > max(40, 70 - score // 5):
            spawn_group(obstacles)
            spawn_timer = 0
            score += 1
            if score > high_score:
                high_score = score
                save_high_score(high_score)

        for o in obstacles[:]:
            o.update(speed)
            if o.hitbox().colliderect(player.hitbox()):
                dead = True
                pygame.mixer.music.stop()
                if death_sound: death_sound.play()
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
    
    for o in obstacles[:]:
        o.draw()
    obstacles = [o for o in obstacles if o.x > -50]
    player.draw()
    
    if dead:
        draw_game_over(score, high_score)
    else:
        draw_score(score, high_score)

    pygame.display.update()
    clock.tick(60)
            
