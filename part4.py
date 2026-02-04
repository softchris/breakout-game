# Part 4 - Game Mechanics & Scoring
# ===================================
# Features added from part3:
# - Ball class for tracking individual balls
# - Multi-ball system (game continues while any ball remains)
# - Bonus ball spawn (1/5 chance when destroying a block)
# - Angle-based paddle bounce (ball direction depends on hit position)
# - Paddle spin effect (paddle movement affects ball trajectory)
# - Game over when all balls are lost (shows GAME OVER on menu)
# - Win condition when all blocks destroyed
# - High score system with CSV file storage
# - Name entry screen after winning
# - High Scores menu option showing top 10 scores
# - Ball count display in HUD

import pygame
import random
import math
import os
import csv
from datetime import datetime

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout")

# High score file
HIGHSCORE_FILE = "highscores.csv"

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
GOLD = (255, 215, 0)

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

# Particle system
particles = []  # Ball trail particles
explosion_particles = []  # Block explosion particles

# Fire colors for comet and explosion
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
    global blocks, balls, paddle_x, start_time, particles, explosion_particles
    global game_over, game_won, final_time
    blocks = create_blocks()
    balls = [Ball(WIDTH // 2, HEIGHT // 2, 4, -4)]
    paddle_x = (WIDTH - paddle_width) // 2
    start_time = pygame.time.get_ticks()
    particles = []
    explosion_particles = []
    game_over = False
    game_won = False
    final_time = 0

# High score functions
def load_highscores():
    """Load high scores from CSV file"""
    scores = []
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scores.append({
                        'name': row['name'],
                        'time': int(row['time']),
                        'date': row['date']
                    })
        except:
            pass
    # Sort by time (ascending - lower is better)
    scores.sort(key=lambda x: x['time'])
    return scores[:10]  # Return top 10

# 5) Save high scores to CSV file
def save_highscore(name, time_seconds):
    """Save a new high score to CSV file"""
    scores = []
    # Read existing scores
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scores.append(row)
        except:
            pass
    
    # Add new score
    scores.append({
        'name': name,
        'time': str(time_seconds),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    
    # Write all scores back
    with open(HIGHSCORE_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'time', 'date'])
        writer.writeheader()
        writer.writerows(scores)

# 2. Create blocks
blocks = create_blocks()

# Paddle settings
paddle_width, paddle_height = 100, 15
paddle_x = (WIDTH - paddle_width) // 2
paddle_y = HEIGHT - 40
paddle_speed = 8
paddle_velocity = 0  # Track paddle movement for spin

# Ball settings
ball_size = 15

# 1) Ball class for multi-ball support
class Ball:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, ball_size, ball_size)

# Initialize balls list
balls = [Ball(WIDTH // 2, HEIGHT // 2, 4, -4)]

# Game state
game_paused = False
show_credits = False
show_highscores = False
game_over = False
game_won = False
entering_name = False
player_name = ""
final_time = 0
start_time = pygame.time.get_ticks()

# Menu button class
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

# Create menu buttons
btn_new_game = Button(WIDTH // 2, HEIGHT // 2 - 80, 200, 50, "New Game")
btn_highscores = Button(WIDTH // 2, HEIGHT // 2 - 10, 200, 50, "High Scores", ORANGE)
btn_credits = Button(WIDTH // 2, HEIGHT // 2 + 60, 200, 50, "Credits")
btn_back = Button(WIDTH // 2, HEIGHT // 2 + 150, 200, 50, "Back", GRAY)

def draw_menu():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Title - show different title based on game state
    if game_over:
        title = font_large.render("GAME OVER", True, RED)
    elif game_won:
        title = font_large.render("YOU WIN!", True, GREEN)
    else:
        title = font_large.render("PAUSED", True, YELLOW)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title, title_rect)
    
    # Buttons
    btn_new_game.draw(screen)
    btn_highscores.draw(screen)
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

def draw_highscores():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))
    
    # Title
    title = font_large.render("HIGH SCORES", True, GOLD)
    title_rect = title.get_rect(center=(WIDTH // 2, 60))
    screen.blit(title, title_rect)
    
    # Load and display scores
    scores = load_highscores()
    
    if not scores:
        no_scores = font_medium.render("No scores yet!", True, GRAY)
        no_scores_rect = no_scores.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(no_scores, no_scores_rect)
    else:
        # Header
        header = font_small.render("RANK    NAME              TIME         DATE", True, YELLOW)
        screen.blit(header, (100, 110))
        
        # Scores
        for i, score in enumerate(scores[:10]):
            rank = i + 1
            name = score['name'][:12].ljust(12)
            time_sec = int(score['time'])
            mins = time_sec // 60
            secs = time_sec % 60
            time_str = f"{mins:02d}:{secs:02d}"
            date = score['date']
            
            # Color based on rank
            if rank == 1:
                color = GOLD
            elif rank == 2:
                color = (192, 192, 192)  # Silver
            elif rank == 3:
                color = (205, 127, 50)   # Bronze
            else:
                color = WHITE
            
            line = f" {rank:2d}.     {name}      {time_str}      {date}"
            score_text = font_small.render(line, True, color)
            screen.blit(score_text, (100, 145 + i * 35))
    
    # Back button
    btn_back.draw(screen)

def draw_name_entry():
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))
    
    # Title
    title = font_large.render("YOU WIN!", True, GREEN)
    title_rect = title.get_rect(center=(WIDTH // 2, 100))
    screen.blit(title, title_rect)
    
    # Time
    mins = final_time // 60
    secs = final_time % 60
    time_text = font_medium.render(f"Your time: {mins:02d}:{secs:02d}", True, YELLOW)
    time_rect = time_text.get_rect(center=(WIDTH // 2, 180))
    screen.blit(time_text, time_rect)
    
    # Prompt
    prompt = font_medium.render("Enter your name:", True, WHITE)
    prompt_rect = prompt.get_rect(center=(WIDTH // 2, 260))
    screen.blit(prompt, prompt_rect)
    
    # Name input box
    box_width = 300
    box_height = 50
    box_x = WIDTH // 2 - box_width // 2
    box_y = 300
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 3, border_radius=5)
    
    # Player name text
    name_surface = font_medium.render(player_name + "_", True, CYAN)
    name_rect = name_surface.get_rect(center=(WIDTH // 2, box_y + box_height // 2))
    screen.blit(name_surface, name_rect)
    
    # Instructions
    instr = font_small.render("Press ENTER to save", True, GRAY)
    instr_rect = instr.get_rect(center=(WIDTH // 2, 400))
    screen.blit(instr, instr_rect)

def draw_hud():
    # Blocks left and ball count
    blocks_left = len(blocks)
    blocks_text = font_small.render(f"Blocks: {blocks_left}/{total_blocks}", True, WHITE)
    screen.blit(blocks_text, (10, HEIGHT - 30))
    
    # Ball count
    ball_count = len(balls)
    ball_text = font_small.render(f"Balls: {ball_count}", True, CYAN if ball_count > 1 else WHITE)
    screen.blit(ball_text, (10, HEIGHT - 60))
    
    # Time elapsed
    if game_over or game_won:
        elapsed_ms = pause_time - start_time
    elif not game_paused:
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
            # Name entry mode
            if entering_name:
                if event.key == pygame.K_RETURN and player_name:
                    # Save score and go to menu
                    save_highscore(player_name, final_time)
                    entering_name = False
                    game_paused = True
                    player_name = ""
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.unicode.isalnum() or event.unicode == ' ':
                    if len(player_name) < 12:
                        player_name += event.unicode
            else:
                if event.key == pygame.K_ESCAPE:
                    if show_credits or show_highscores:
                        show_credits = False
                        show_highscores = False
                    elif game_over or game_won:
                        # Can't unpause if game is over
                        pass
                    else:
                        game_paused = not game_paused
                        if game_paused:
                            pause_time = pygame.time.get_ticks()
                        else:
                            # Adjust start_time to account for pause duration
                            start_time += pygame.time.get_ticks() - pause_time
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_paused and not show_credits and not show_highscores and not entering_name:
                if btn_new_game.is_clicked(mouse_pos):
                    reset_game()
                    game_paused = False
                elif btn_highscores.is_clicked(mouse_pos):
                    show_highscores = True
                elif btn_credits.is_clicked(mouse_pos):
                    show_credits = True
            elif show_credits or show_highscores:
                if btn_back.is_clicked(mouse_pos):
                    show_credits = False
                    show_highscores = False
    
    # Update button hover states
    if game_paused and not show_credits and not show_highscores and not entering_name:
        btn_new_game.check_hover(mouse_pos)
        btn_highscores.check_hover(mouse_pos)
        btn_credits.check_hover(mouse_pos)
    elif show_credits or show_highscores:
        btn_back.check_hover(mouse_pos)
    
    if not game_paused and not game_over and not game_won and not entering_name:
        # Paddle movement
        keys = pygame.key.get_pressed()
        paddle_velocity = 0  # Reset each frame
        if keys[pygame.K_LEFT] and paddle_x > 0:
            paddle_x -= paddle_speed
            paddle_velocity = -paddle_speed
        if keys[pygame.K_RIGHT] and paddle_x < WIDTH - paddle_width:
            paddle_x += paddle_speed
            paddle_velocity = paddle_speed

        # Update all balls
        balls_to_remove = []
        new_balls = []
        
        for ball in balls:
            # Ball movement
            ball.update()
            
            # Create comet trail particles
            particles.extend(create_comet_trail(ball.x + ball_size // 2, ball.y + ball_size // 2, ball.dx, ball.dy))

            # Ball collision with walls
            if ball.x <= 0 or ball.x >= WIDTH - ball_size:
                ball.dx = -ball.dx
            if ball.y <= 0:
                ball.dy = -ball.dy

            # Ball collision with paddle
            if (ball.y + ball_size >= paddle_y and 
                ball.y + ball_size <= paddle_y + paddle_height and
                ball.x + ball_size >= paddle_x and 
                ball.x <= paddle_x + paddle_width):
                
                # 2) Angle based on where ball hits paddle
                ball_center = ball.x + ball_size // 2
                hit_pos = (ball_center - paddle_x) / paddle_width
                
                # Convert to angle: -1 (far left) to 1 (far right)
                # Center (0.5) = 0, meaning straight up
                angle_factor = (hit_pos - 0.5) * 2
                
                # Set new dx based on hit position, max speed of 6
                ball.dx = angle_factor * 6
                
                # 3) Paddle movement adds spin to ball
                spin = -paddle_velocity * 0.3
                ball.dx += spin
                
                # Clamp horizontal speed to prevent crazy angles
                ball.dx = max(-8, min(8, ball.dx))
                
                # Ensure ball goes up and maintain consistent speed
                speed = math.sqrt(ball.dx ** 2 + ball.dy ** 2)
                ball.dy = -abs(math.sqrt(max(16, speed ** 2 - ball.dx ** 2)))  # Minimum vertical speed
                
                ball.y = paddle_y - ball_size  # Prevent sticking

            # Ball collision with blocks
            ball_rect = ball.get_rect()
            for block in blocks[:]:
                if ball_rect.colliderect(block["rect"]):
                    # Get block center
                    cx = block["rect"].centerx
                    cy = block["rect"].centery
                    
                    # Create fiery explosion
                    explosion_particles.extend(create_fiery_explosion(cx, cy))
                    
                    # 4) 1/5 chance to spawn bonus ball
                    if random.randint(1, 5) == 1:
                        new_balls.append(Ball(cx, cy, 0, 4))
                    
                    blocks.remove(block)
                    ball.dy = -ball.dy
                    break

            # Ball falls off bottom - mark for removal
            if ball.y > HEIGHT:
                balls_to_remove.append(ball)
        
        # Remove lost balls and add new ones
        for ball in balls_to_remove:
            balls.remove(ball)
        balls.extend(new_balls)
        
        # GAME OVER only if ALL balls are lost
        if len(balls) == 0:
            game_over = True
            game_paused = True
            pause_time = pygame.time.get_ticks()
        
        # Check for win condition
        if len(blocks) == 0:
            game_won = True
            entering_name = True
            final_time = (pygame.time.get_ticks() - start_time) // 1000
        
        # Update particles
        particles = [p for p in particles if p.update()]
        explosion_particles = [p for p in explosion_particles if p.update()]

    # Draw everything
    screen.fill(BLACK)
    
    # Draw particles (behind other objects)
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
    
    # Draw all balls with fiery glow effect
    for ball in balls:
        glow_size = ball_size + 8
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        # Outer orange glow
        pygame.draw.circle(glow_surface, (255, 100, 0, 40), (glow_size, glow_size), glow_size)
        # Inner yellow glow
        pygame.draw.circle(glow_surface, (255, 200, 50, 60), (glow_size, glow_size), glow_size - 3)
        # White core glow
        pygame.draw.circle(glow_surface, (255, 255, 200, 80), (glow_size, glow_size), glow_size - 6)
        screen.blit(glow_surface, (ball.x - glow_size + ball_size // 2, ball.y - glow_size + ball_size // 2))
        # Main ball - white hot center
        pygame.draw.ellipse(screen, (255, 255, 240), (ball.x, ball.y, ball_size, ball_size))
    
    # Draw HUD
    draw_hud()
    
    # Draw menu/overlays based on state
    if entering_name:
        draw_name_entry()
    elif game_paused and not show_credits and not show_highscores:
        draw_menu()
    elif show_credits:
        draw_credits()
    elif show_highscores:
        draw_highscores()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
