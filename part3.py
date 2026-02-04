# Part 3 - Visual Effects & Menu System
# =====================================
# Features added from part2:
# - Particle system for ball trail (comet tail effect)
# - Fiery explosion particles when blocks are destroyed
# - Multiple particle types: CometParticle, FireParticle, SparkParticle, EmberParticle
# - HUD displaying blocks remaining and elapsed time
# - Game menu (toggle with ESC key)
# - Menu options: New Game, Credits
# - Credits screen showing author info
# - Game pause functionality

import pygame
import random
import math

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)

# Fonts
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

# 1. Block settings
block_width, block_height = 75, 20
block_rows = 4
block_cols = 10
block_padding = 5
block_top_offset = 50
total_blocks = block_rows * block_cols

# 1) Particle system for visual effects
particles = []  # Ball trail particles
explosion_particles = []  # Block explosion particles

FIRE_COLORS = [
    (255, 255, 255),  # White hot core
    (255, 255, 200),  # Light yellow
    (255, 255, 100),  # Yellow
    (255, 200, 50),   # Golden
    (255, 150, 0),    # Orange
    (255, 100, 0),    # Deep orange
    (255, 50, 0),     # Red-orange
    (200, 30, 0),     # Dark red
    (150, 20, 0),     # Ember
]

class Particle:
    def __init__(self, x, y, color, size=3, lifetime=20, dx=0, dy=0, gravity=0, shrink=True):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.dx = dx
        self.dy = dy
        self.gravity = gravity
        self.shrink = shrink
    
    def update(self):
        self.lifetime -= 1
        self.x += self.dx
        self.y += self.dy
        self.dy += self.gravity
        self.dx *= 0.98  # Drag
        return self.lifetime > 0
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        if self.shrink:
            current_size = max(1, int(self.size * alpha))
        else:
            current_size = self.size
        color = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), current_size)

class CometParticle(Particle):
    """Special particle for comet tail with color transition"""
    def __init__(self, x, y, dx, dy, size=4, lifetime=35):
        super().__init__(x, y, FIRE_COLORS[0], size, lifetime, dx * 0.1, dy * 0.1, gravity=0)
        self.base_size = size
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        # Color transitions from white -> yellow -> orange -> red based on lifetime
        color_index = int((1 - alpha) * (len(FIRE_COLORS) - 1))
        color_index = min(color_index, len(FIRE_COLORS) - 1)
        base_color = FIRE_COLORS[color_index]
        
        # Apply alpha to color
        color = tuple(max(0, min(255, int(c * (0.3 + alpha * 0.7)))) for c in base_color)
        current_size = max(1, int(self.base_size * alpha))
        
        # Draw glow
        if current_size > 2:
            glow_color = tuple(max(0, min(255, int(c * 0.3))) for c in base_color)
            pygame.draw.circle(surface, glow_color, (int(self.x), int(self.y)), current_size + 2)
        
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), current_size)

class FireParticle(Particle):
    """Fiery explosion particle with flickering effect"""
    def __init__(self, x, y, dx, dy, size=5, lifetime=45):
        super().__init__(x, y, FIRE_COLORS[0], size, lifetime, dx, dy, gravity=0.15)
        self.flicker = random.uniform(0.8, 1.2)
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        # Color transitions through fire colors
        color_index = int((1 - alpha) * (len(FIRE_COLORS) - 1))
        color_index = min(color_index, len(FIRE_COLORS) - 1)
        base_color = FIRE_COLORS[color_index]
        
        # Flickering brightness
        flicker = random.uniform(0.85, 1.15)
        color = tuple(max(0, min(255, int(c * alpha * flicker))) for c in base_color)
        current_size = max(1, int(self.size * (0.3 + alpha * 0.7)))
        
        # Draw outer glow
        if current_size > 2 and alpha > 0.3:
            glow_size = current_size + 3
            glow_color = tuple(max(0, min(255, int(c * 0.4 * alpha))) for c in base_color)
            pygame.draw.circle(surface, glow_color, (int(self.x), int(self.y)), glow_size)
        
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), current_size)

class SparkParticle(Particle):
    """Small bright spark that flies fast"""
    def __init__(self, x, y, dx, dy):
        color = random.choice([(255, 255, 255), (255, 255, 200), (255, 200, 100)])
        super().__init__(x, y, color, size=2, lifetime=random.randint(15, 30), dx=dx, dy=dy, gravity=0.2)
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        color = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
        # Draw as a small line/streak for sparks
        end_x = self.x - self.dx * 2
        end_y = self.y - self.dy * 2
        pygame.draw.line(surface, color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), 2)

class EmberParticle(Particle):
    """Slow-falling ember that glows"""
    def __init__(self, x, y):
        color = random.choice([(255, 100, 0), (255, 150, 50), (200, 50, 0)])
        dx = random.uniform(-0.5, 0.5)
        dy = random.uniform(-2, -0.5)
        super().__init__(x, y, color, size=random.randint(2, 4), lifetime=random.randint(40, 70), dx=dx, dy=dy, gravity=0.05)
        self.pulse = random.uniform(0, math.pi * 2)
    
    def update(self):
        self.pulse += 0.2
        return super().update()
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        pulse_factor = 0.7 + 0.3 * math.sin(self.pulse)
        color = tuple(max(0, min(255, int(c * alpha * pulse_factor))) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)

# 2) Comet tail effect behind the ball
def create_comet_trail(x, y, ball_dx, ball_dy):
    """Create multiple particles for comet tail effect"""
    new_particles = []
    # Create 3-5 particles per frame for dense trail
    for _ in range(random.randint(3, 5)):
        # Particles spawn slightly behind the ball
        offset_x = random.uniform(-4, 4) - ball_dx * 0.5
        offset_y = random.uniform(-4, 4) - ball_dy * 0.5
        size = random.randint(3, 7)
        lifetime = random.randint(25, 45)
        new_particles.append(CometParticle(
            x + offset_x, y + offset_y,
            ball_dx, ball_dy,
            size=size, lifetime=lifetime
        ))
    return new_particles

# 3) Fiery explosion when blocks are destroyed
def create_fiery_explosion(x, y):
    """Create a spectacular fiery explosion"""
    new_particles = []
    
    # Main fire burst - 25 fire particles
    for _ in range(25):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed - 1  # Bias upward
        size = random.randint(4, 10)
        lifetime = random.randint(30, 55)
        new_particles.append(FireParticle(x, y, dx, dy, size, lifetime))
    
    # Flying sparks - 15 fast bright sparks
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 12)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        new_particles.append(SparkParticle(x, y, dx, dy))
    
    # Falling embers - 10 slow glowing embers
    for _ in range(10):
        offset_x = random.uniform(-20, 20)
        offset_y = random.uniform(-10, 10)
        new_particles.append(EmberParticle(x + offset_x, y + offset_y))
    
    return new_particles

def create_blocks():
    blocks = []
    block_colors = [RED, ORANGE, GREEN, BLUE]
    for row in range(block_rows):
        for col in range(block_cols):
            block_x = col * (block_width + block_padding) + block_padding
            block_y = row * (block_height + block_padding) + block_top_offset
            block_rect = pygame.Rect(block_x, block_y, block_width, block_height)
            blocks.append({"rect": block_rect, "color": block_colors[row % len(block_colors)]})
    return blocks

def reset_game():
    global blocks, ball_x, ball_y, ball_dx, ball_dy, paddle_x, start_time
    global particles, explosion_particles
    blocks = create_blocks()
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    ball_dx = 4
    ball_dy = -4
    paddle_x = (WIDTH - paddle_width) // 2
    start_time = pygame.time.get_ticks()
    particles = []
    explosion_particles = []

# 2. Create blocks
blocks = create_blocks()

# Paddle settings
paddle_width, paddle_height = 100, 15
paddle_x = (WIDTH - paddle_width) // 2
paddle_y = HEIGHT - 40
paddle_speed = 8

# Ball settings
ball_size = 15
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_dx = 4
ball_dy = -4

# 4) Game menu system (ESC to toggle)
game_paused = False
show_credits = False
start_time = pygame.time.get_ticks()

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(255, c + 50) for c in color)
        self.is_hovered = False
    
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)
        text_surface = font_medium.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

btn_new_game = Button(WIDTH // 2, HEIGHT // 2 - 40, 200, 50, "New Game")
btn_credits = Button(WIDTH // 2, HEIGHT // 2 + 30, 200, 50, "Credits")
btn_back = Button(WIDTH // 2, HEIGHT // 2 + 100, 200, 50, "Back", GRAY)

def draw_menu():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Title
    title = font_large.render("PAUSED", True, YELLOW)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title, title_rect)
    
    # Buttons
    btn_new_game.draw(screen)
    btn_credits.draw(screen)

def draw_credits():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    # Credits title
    title = font_large.render("CREDITS", True, CYAN)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title, title_rect)
    
    # Credit text
    credit1 = font_medium.render("Created by Chris", True, WHITE)
    credit1_rect = credit1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
    screen.blit(credit1, credit1_rect)
    
    credit2 = font_medium.render("using pygame and Python", True, WHITE)
    credit2_rect = credit2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(credit2, credit2_rect)
    
    # Back button
    btn_back.draw(screen)

def draw_hud():
    # Blocks left
    blocks_left = len(blocks)
    blocks_text = font_small.render(f"Blocks: {blocks_left}/{total_blocks}", True, WHITE)
    screen.blit(blocks_text, (10, HEIGHT - 30))
    
    # Time elapsed
    if not game_paused:
        elapsed_ms = pygame.time.get_ticks() - start_time
    else:
        elapsed_ms = pause_time - start_time
    elapsed_sec = elapsed_ms // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    time_text = font_small.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
    screen.blit(time_text, (WIDTH - 150, HEIGHT - 30))
    
    # Press ESC hint
    esc_text = font_small.render("ESC - Menu", True, GRAY)
    screen.blit(esc_text, (WIDTH // 2 - 50, HEIGHT - 30))

# Game loop
clock = pygame.time.Clock()
running = True
pause_time = 0

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if show_credits:
                    show_credits = False
                else:
                    game_paused = not game_paused
                    if game_paused:
                        pause_time = pygame.time.get_ticks()
                    else:
                        # Adjust start_time to account for pause duration
                        start_time += pygame.time.get_ticks() - pause_time
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_paused and not show_credits:
                if btn_new_game.is_clicked(mouse_pos):
                    reset_game()
                    game_paused = False
                elif btn_credits.is_clicked(mouse_pos):
                    show_credits = True
            elif show_credits:
                if btn_back.is_clicked(mouse_pos):
                    show_credits = False
    
    # Update button hover states
    if game_paused and not show_credits:
        btn_new_game.check_hover(mouse_pos)
        btn_credits.check_hover(mouse_pos)
    elif show_credits:
        btn_back.check_hover(mouse_pos)
    
    if not game_paused:
        # Paddle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and paddle_x > 0:
            paddle_x -= paddle_speed
        if keys[pygame.K_RIGHT] and paddle_x < WIDTH - paddle_width:
            paddle_x += paddle_speed

        # Ball movement
        ball_x += ball_dx
        ball_y += ball_dy
        
        particles.extend(create_comet_trail(ball_x + ball_size // 2, ball_y + ball_size // 2, ball_dx, ball_dy))

        # Ball collision with walls
        if ball_x <= 0 or ball_x >= WIDTH - ball_size:
            ball_dx = -ball_dx
        if ball_y <= 0:
            ball_dy = -ball_dy

        # Ball collision with paddle
        if (ball_y + ball_size >= paddle_y and 
            ball_y + ball_size <= paddle_y + paddle_height and
            ball_x + ball_size >= paddle_x and 
            ball_x <= paddle_x + paddle_width):
            ball_dy = -ball_dy
            ball_y = paddle_y - ball_size  # Prevent sticking

        # 3. Ball collision with blocks
        ball_rect = pygame.Rect(ball_x, ball_y, ball_size, ball_size)
        for block in blocks[:]:
            if ball_rect.colliderect(block["rect"]):
                cx = block["rect"].centerx
                cy = block["rect"].centery
                explosion_particles.extend(create_fiery_explosion(cx, cy))
                
                blocks.remove(block)
                ball_dy = -ball_dy
                break

        # Ball falls off bottom - reset
        if ball_y > HEIGHT:
            ball_x = WIDTH // 2
            ball_y = HEIGHT // 2
            ball_dy = -4
        
        particles = [p for p in particles if p.update()]
        explosion_particles = [p for p in explosion_particles if p.update()]

    # Draw everything
    screen.fill(BLACK)
    
    for p in particles:
        p.draw(screen)
    for p in explosion_particles:
        p.draw(screen)
    
    # 4. Draw blocks
    for block in blocks:
        pygame.draw.rect(screen, block["color"], block["rect"])
        # Add subtle highlight
        highlight_rect = pygame.Rect(block["rect"].x, block["rect"].y, block["rect"].width, 3)
        highlight_color = tuple(min(255, c + 60) for c in block["color"])
        pygame.draw.rect(screen, highlight_color, highlight_rect)
    
    pygame.draw.rect(screen, BLUE, (paddle_x, paddle_y, paddle_width, paddle_height))
    
    # 5) Ball with fiery glow effect
    glow_size = ball_size + 8
    glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
    # Outer orange glow
    pygame.draw.circle(glow_surface, (255, 100, 0, 40), (glow_size, glow_size), glow_size)
    # Inner yellow glow
    pygame.draw.circle(glow_surface, (255, 200, 50, 60), (glow_size, glow_size), glow_size - 3)
    # White core glow
    pygame.draw.circle(glow_surface, (255, 255, 200, 80), (glow_size, glow_size), glow_size - 6)
    screen.blit(glow_surface, (ball_x - glow_size + ball_size // 2, ball_y - glow_size + ball_size // 2))
    # Main ball - white hot center
    pygame.draw.ellipse(screen, (255, 255, 240), (ball_x, ball_y, ball_size, ball_size))
    
    draw_hud()
    
    if game_paused and not show_credits:
        draw_menu()
    elif show_credits:
        draw_credits()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
