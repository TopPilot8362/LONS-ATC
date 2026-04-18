import pygame
import math
import random
import sys

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Euroscope-style ATC - London Control South Sector")

# Colors and fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
font = pygame.font.SysFont("Arial", 14)

# Load background map (placeholder: plain background)
# Replace with actual map image path if available
# background_img = pygame.image.load("sector_map.png")

# Aircraft class with routing & waypoints
class Aircraft:
    def __init__(self, id, x, y, altitude=30000, heading=0, speed=3):
        self.id = id
        self.x = x
        self.y = y
        self.altitude = altitude
        self.heading = heading
        self.speed = speed
        self.waypoints = []  # list of (x, y)
        self.selected = False
        self.message_log = []

    def set_route(self, waypoints):
        self.waypoints = waypoints

    def update_position(self):
        if self.waypoints:
            target_x, target_y = self.waypoints[0]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)
            if distance < self.speed:
                self.x, self.y = target_x, target_y
                self.waypoints.pop(0)
            else:
                self.heading = math.degrees(math.atan2(dy, dx))
                rad = math.radians(self.heading)
                self.x += self.speed * math.cos(rad)
                self.y += self.speed * math.sin(rad)
        else:
            # Continue current heading
            rad = math.radians(self.heading)
            self.x += self.speed * math.cos(rad)
            self.y += self.speed * math.sin(rad)

        # Wrap around
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, surface):
        color = GREEN if self.selected else BLUE
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 8)
        # Heading indicator
        end_x = self.x + 15 * math.cos(math.radians(self.heading))
        end_y = self.y + 15 * math.sin(math.radians(self.heading))
        pygame.draw.line(surface, WHITE, (self.x, self.y), (end_x, end_y), 2)
        # Show info if selected
        if self.selected:
            info = f"AC {self.id} | Alt: {self.altitude} ft | HDG: {int(self.heading)}°"
            surface.blit(font.render(info, True, WHITE), (self.x + 10, self.y - 20))

# Message Log System
class MessageLog:
    def __init__(self):
        self.messages = []

    def add_message(self, sender, text):
        self.messages.append(f"{sender}: {text}")
        if len(self.messages) > 20:
            self.messages.pop(0)

    def draw(self, surface):
        box = pygame.Rect(10, HEIGHT - 210, 400, 200)
        pygame.draw.rect(surface, BLACK, box)
        pygame.draw.rect(surface, WHITE, box, 2)
        for i, msg in enumerate(self.messages):
            msg_surf = font.render(msg, True, WHITE)
            surface.blit(msg_surf, (20, HEIGHT - 200 + i * 10))

# Conflict detection
def detect_conflicts(aircrafts):
    conflicts = []
    for i in range(len(aircrafts)):
        for j in range(i+1, len(aircrafts)):
            ac1 = aircrafts[i]
            ac2 = aircrafts[j]
            dist = math.hypot(ac1.x - ac2.x, ac1.y - ac2.y)
            alt_diff = abs(ac1.altitude - ac2.altitude)
            if dist < 50 and alt_diff < 1000:
                conflicts.append((ac1, ac2))
    return conflicts

def handle_conflicts(conflicts, message_log):
    for ac1, ac2 in conflicts:
        message_log.add_message("Conflict", f"AC {ac1.id} & AC {ac2.id} conflict!")
        # Optional: instruct aircraft to climb or turn

# Process user commands
def process_command(ac, command):
    parts = command.lower().split()
    if not parts:
        return
    if parts[0] == "alt":
        try:
            ac.altitude = int(parts[1])
        except:
            pass
    elif parts[0] in ("h", "heading"):
        try:
            ac.heading = int(parts[1]) % 360
        except:
            pass
    elif parts[0] == "speed":
        try:
            ac.speed = int(parts[1])
        except:
            pass
    elif parts[0] == "route":
        waypoints = []
        for wp in parts[1:]:
            try:
                x_str, y_str = wp.split(',')
                x, y = int(x_str), int(y_str)
                waypoints.append((x, y))
            except:
                continue
        ac.set_route(waypoints)
    elif parts[0] == "hold":
        # Implement hold pattern (hold at current position)
        ac.set_route([(ac.x, ac.y)] * 3)  # simple hold
    elif parts[0] == "clear":
        ac.waypoints = []

# Utility to get aircraft at position
def get_aircraft_at_pos(pos):
    for ac in aircraft_list:
        dist = math.hypot(ac.x - pos[0], ac.y - pos[1])
        if dist < 10:
            return ac
    return None

# Initialize aircraft list
aircraft_list = []
for i in range(10):
    x = random.randint(100, WIDTH - 100)
    y = random.randint(100, HEIGHT - 100)
    heading = random.randint(0, 359)
    aircraft_list.append(Aircraft(i, x, y, heading=heading))

# Initialize message log
message_log = MessageLog()

# Command input variables
selected_aircraft = None
command_mode = False
command_text = ""

# Load sound for alerts
try:
    alert_sound = pygame.mixer.Sound("alert.wav")
except:
    alert_sound = None

# Main loop
clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            ac = get_aircraft_at_pos(pygame.mouse.get_pos())
            if ac:
                if selected_aircraft:
                    selected_aircraft.selected = False
                ac.selected = True
                selected_aircraft = ac

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                command_mode = True
                command_text = ""
            elif command_mode:
                if event.key == pygame.K_RETURN:
                    if selected_aircraft:
                        process_command(selected_aircraft, command_text)
                        message_log.add_message("ATC", f"Command: {command_text}")
                    command_mode = False
                elif event.key == pygame.K_BACKSPACE:
                    command_text = command_text[:-1]
                else:
                    command_text += event.unicode
            elif event.key == pygame.K_SPACE:
                # Optional: add random commands or toggle features
                pass

    # Update aircraft positions
    for ac in aircraft_list:
        ac.update_position()

    # Detect conflicts
    conflicts = detect_conflicts(aircraft_list)
    if conflicts and alert_sound:
        alert_sound.play()
    handle_conflicts(conflicts, message_log)

    # Draw everything
    screen.fill(BLACK)
    # If you have a map, blit it here
    # screen.blit(background_img, (0,0))
    # Draw sector boundary
    pygame.draw.rect(screen, WHITE, (50, 50, WIDTH - 100, HEIGHT - 100), 2)

    for ac in aircraft_list:
        ac.draw(screen)

    # Draw message log
    message_log.draw(screen)

    # Draw command input box
    if command_mode:
        input_box = pygame.Rect(20, HEIGHT - 40, 400, 30)
        pygame.draw.rect(screen, WHITE, input_box)
        txt_surface = font.render(command_text, True, BLACK)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        instruction_text = "Enter command (alt, heading, speed, route x,y ...):"
        instruction_surf = font.render(instruction_text, True, WHITE)
        screen.blit(instruction_surf, (20, HEIGHT - 60))
    else:
        info_text = "Press 'C' to enter command mode | SPACE for random commands"
        info_surf = font.render(info_text, True, WHITE)
        screen.blit(info_surf, (20, HEIGHT - 40))

    # Optional: display selected aircraft info
    if selected_aircraft:
        info_str = f"Selected AC {selected_aircraft.id} | Alt: {selected_aircraft.altitude} ft | HDG: {int(selected_aircraft.heading)}° | SPD: {selected_aircraft.speed}"
        info_surf = font.render(info_str, True, WHITE)
        screen.blit(info_surf, (650, HEIGHT - 40))

    pygame.display.flip()

pygame.quit()
