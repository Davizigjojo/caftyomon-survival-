import pygame
import random
import os
import sys

pygame.init()

WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

DEBUG_HITBOX = False

GROUND_Y = HEIGHT - 80
PLAYER_Y_ON_GROUND = GROUND_Y - 16

# Caminho relativo (funciona no navegador)
BASE_PATH = os.path.dirname(__file__)

def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(BASE_PATH, name))
    except:
        return None

def load_image(name, size=None):
    try:
        img = pygame.image.load(os.path.join(BASE_PATH, name)).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except:
        return None

def load_music(name):
    try:
        pygame.mixer.music.load(os.path.join(BASE_PATH, name))
        return True
    except:
        return False

jump_sound = load_sound("jump.wav")
death_sound = load_sound("death.wav")
cube_img = load_image("player.png", (32, 32))
spike_img = load_image("spike.png", (32, 32))
mini_img = load_image("mini-spike.png", (32, 16))

def start_music():
    if load_music("music.wav"):
        pygame.mixer.music.play(-1)

# Pygbag só toca música após clique
music_started = False


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
            if jump_sound:
                jump_sound.play()

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


class Spike:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - 32

    def update(self, s):
        self.x -= s

    def hitbox(self):
        return pygame.Rect(self.x + 8, self.y + 8, 16, 24)

    def draw(self):
        if spike_img:
            screen.blit(spike_img, (self.x, self.y))


class MiniSpike(Spike):
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - 16

    def hitbox(self):
        return pygame.Rect(self.x + 10, self.y + 4, 12, 12)

    def draw(self):
        if mini_img:
            screen.blit(mini_img, (self.x, self.y))


def spawn_group(obs):
    t = random.randint(1, 6)
    base = WIDTH + 50
    if t <= 3:
        obs.append(Spike(base))
    elif t == 4:
        obs.append(Spike(base))
        obs.append(Spike(base + 32))
    elif t == 5:
        obs.append(Spike(base))
        obs.append(Spike(base + 32))
        obs.append(Spike(base + 64))
    else:
        obs.append(MiniSpike(base))


def draw_game_over(score, high):
    font = pygame.font.SysFont("Arial", 38)
    t = font.render("GAME OVER", True, (255, 50, 50))
    s = font.render(f"SCORE: {score}", True, (255, 255, 255))
    r = font.render(f"RECORD: {high}", True, (255, 255, 0))

    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
    screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2))
    screen.blit(r, (WIDTH//2 - r.get_width()//2, HEIGHT//2 + 50))


def menu():
    font = pygame.font.SysFont("Arial", 38)
    while True:
        screen.fill((30, 30, 30))

        title = font.render("Geometry Dash Web Edition", True, (255, 255, 255))
        subtitle = font.render("Toque para começar", True, (255, 255, 0))

        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 170))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                return


menu()

player = Player()
obstacles = []
score = 0
highscore = 0
spawn_timer = 0
dead = False

while True:
    
    
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            if not music_started:
                start_music()
                music_started = True

            if dead:
                obstacles.clear()
                score = 0
                dead = False
            else:
                player.jump()

    screen.fill((80, 40, 80))
    pygame.draw.rect(screen, (40, 40, 40), (0, GROUND_Y, WIDTH, 80))

    if not dead:
        player.update()
        spawn_timer += 1

        if spawn_timer > 50:
            spawn_group(obstacles)
            spawn_timer = 0
            score += 1
            if score > highscore:
                highscore = score

    for o in obstacles:
        o.update(6)
        if o.hitbox().colliderect(player.hitbox()):
            dead = True
            pygame.mixer.music.stop()
            if death_sound:
                death_sound.play()

        o.draw()

    obstacles = [o for o in obstacles if o.x > -50]

    player.draw()

    font = pygame.font.SysFont("Arial", 36)
    s = font.render(str(score), True, (255, 255, 255))
    screen.blit(s, (20, 20))

    if dead:
        draw_game_over(score, highscore)

    pygame.display.update()
    clock.tick(60)