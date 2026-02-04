import pygame

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

# Game loop
clock = pygame.time.Clock()
running = True

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Paddle movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle_x > 0:
        paddle_x -= paddle_speed
    if keys[pygame.K_RIGHT] and paddle_x < WIDTH - paddle_width:
        paddle_x += paddle_speed

    # Ball movement
    ball_x += ball_dx
    ball_y += ball_dy

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

    # Ball falls off bottom - reset
    if ball_y > HEIGHT:
        ball_x = WIDTH // 2
        ball_y = HEIGHT // 2
        ball_dy = -4

    # Draw everything
    screen.fill(BLACK)

    # paddle
    pygame.draw.rect(screen, BLUE, (paddle_x, paddle_y, paddle_width, paddle_height))

    # ball
    pygame.draw.ellipse(screen, WHITE, (ball_x, ball_y, ball_size, ball_size))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
