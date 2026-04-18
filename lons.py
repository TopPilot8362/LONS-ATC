import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image

# Load your map image (replace 'london_sector_map.png' with your actual file)
map_image_path = 'london_sector_map.png'
img = Image.open(map_image_path)

# Convert to array for plotting
img_array = np.array(img)

# Define the sector boundary points (based on the red line in your map)
sector_boundary_points = np.array([
    [215, 115],
    [305, 165],
    [305, 245],
    [215, 305],
    [165, 245],
    [165, 165],
    [215, 115],
    [265, 135],
    [285, 195],
    [265, 265],
    [195, 215],
    [135, 195],
    [115, 135],
    [135, 75],
    [195, 55],
    [265, 75],
    [285, 115],
    [265, 155],
    [215, 135],
    [165, 115],
    [115, 75],
    [135, 35],
    [195, 15],
    [265, 35],
    [285, 75],
    [265, 115],
    [215, 115]
])

# Normalize sector points to match the image scale (assuming your image size)
# Adjust this scaling if needed
scale_x = 1
scale_y = 1
sector_coords = sector_boundary_points * [scale_x, scale_y]

# VOR stations (example positions, adjust as needed)
VORs = {
    'LON': (200, 50),
    'SOU': (400, 300),
    'NORTH': (50, 250)
}

# Aircraft class with waypoints
class Aircraft:
    def __init__(self, id, x, y, heading=0, speed=1):
        self.id = id
        self.x = x
        self.y = y
        self.heading = heading
        self.speed = speed
        self.waypoints = []

    def set_route(self, waypoints):
        self.waypoints = waypoints

    def update(self):
        if self.waypoints:
            target_x, target_y = self.waypoints[0]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = np.hypot(dx, dy)
            if dist < self.speed:
                self.x, self.y = target_x, target_y
                self.waypoints.pop(0)
            else:
                self.heading = np.degrees(np.arctan2(dy, dx))
                rad = np.radians(self.heading)
                self.x += self.speed * np.cos(rad)
                self.y += self.speed * np.sin(rad)
        else:
            rad = np.radians(self.heading)
            self.x += self.speed * np.cos(rad)
            self.y += self.speed * np.sin(rad)

        # Keep aircraft within map bounds
        self.x = np.clip(self.x, 0, img.size[0])
        self.y = np.clip(self.y, 0, img.size[1])

    def draw(self, ax):
        ax.plot(self.x, self.y, 'bo')
        for wp in self.waypoints:
            ax.plot(wp[0], wp[1], 'go')
        if self.waypoints:
            xs = [self.x] + [wp[0] for wp in self.waypoints]
            ys = [self.y] + [wp[1] for wp in self.waypoints]
            ax.plot(xs, ys, 'g--')

# Generate some aircraft with routes
aircrafts = []
for i in range(5):
    x = np.random.uniform(100, img.size[0]-100)
    y = np.random.uniform(100, img.size[1]-100)
    ac = Aircraft(i, x, y, heading=np.random.uniform(0, 360))
    route = [
        (np.random.uniform(50, img.size[0]-50), np.random.uniform(50, img.size[1]-50)),
        (np.random.uniform(50, img.size[0]-50), np.random.uniform(50, img.size[1]-50))
    ]
    ac.set_route(route)
    aircrafts.append(ac)

# Set up plot
fig, ax = plt.subplots(figsize=(10, 8))
ax.imshow(img_array, extent=[0, img.size[0], 0, img.size[1]])
ax.set_xlim(0, img.size[0])
ax.set_ylim(0, img.size[1])
ax.set_title("London South Sector Radar")
ax.set_xlabel("Pixels")
ax.set_ylabel("Pixels")
ax.grid(False)

# Draw sector boundary in red
boundary_line, = ax.plot(sector_coords[:,0], sector_coords[:,1], 'r-', linewidth=2)

# Draw VOR stations
for name, pos in VORs.items():
    ax.plot(pos[0], pos[1], 'r^')
    ax.text(pos[0]+5, pos[1]+5, name, color='red')

# Radar sweep line
sweep_line, = ax.plot([0, 0], [0, img.size[1]], color='green', linewidth=2, alpha=0.7)

# Animation update
def update(frame):
    # Update aircraft positions
    for ac in aircrafts:
        ac.update()

    # Update sweep line angle
    angle = frame % 360
    rad_angle = np.radians(angle)
    x_end = img.size[0] * np.cos(rad_angle)
    y_end = img.size[1] * np.sin(rad_angle)
    sweep_line.set_data([img.size[0]/2, x_end], [img.size[1]/2, y_end])

    # Clear previous aircraft plots
    # Remove previous scatter plots
    [coll.remove() for coll in ax.collections]
    # Plot aircraft
    for ac in aircrafts:
        ac.draw(ax)

    # Detect aircraft in sweep
    detected_x = []
    detected_y = []
    for ac in aircrafts:
        dx = ac.x - img.size[0]/2
        dy = ac.y - img.size[1]/2
        ac_angle = np.degrees(np.arctan2(dy, dx))
        ac_angle = ac_angle % 360
        if abs(ac_angle - angle) < 2:
            detected_x.append(ac.x)
            detected_y.append(ac.y)
    # Plot detected aircraft
    scatter = ax.scatter(detected_x, detected_y, c='red', s=50)

    return sweep_line, scatter

ani = animation.FuncAnimation(fig, update, frames=range(0, 360, 2), interval=50, blit=False)
plt.show()
