import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter
from matplotlib.patches import Circle, Rectangle
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Configuration & Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def polar_to_cartesian(r, theta_deg, center=(0, 0)):
    """
    Convert (r, θ in degrees) to Cartesian (x, y), relative to a given center.
    θ = 0° points to the right (3 o’clock), increasing counterclockwise.
    """
    theta_rad = np.deg2rad(theta_deg)
    x = center[0] + r * np.cos(theta_rad)
    y = center[1] + r * np.sin(theta_rad)
    return x, y

# Watch-face proportions (normalized units)
R_BEZEL = 1.0           # Outer bezel radius
R_DIAL  = 0.90          # Dial radius (a bit inset from bezel)
CENTER  = (0, 0)

# Hour-tick lengths and widths
TICK_LONG   = 0.12
TICK_SHORT  = 0.08
TICK_WIDTH  = 0.015

# Hand lengths (fractions of R_DIAL)
HOUR_HAND_LENGTH   = 0.50
MINUTE_HAND_LENGTH = 0.75
SECOND_HAND_LENGTH = 0.85

# Hand widths (data units; multiplied by 100 when plotting)
HOUR_HAND_WIDTH   = 0.03
MINUTE_HAND_WIDTH = 0.02
SECOND_HAND_WIDTH = 0.005

# Starting “clock time”
START_HOUR   = 12
START_MINUTE = 10
START_SECOND = 30

# Frames per second and total duration
FPS           = 24
ANIM_DURATION = 10       # animation in seconds
TOTAL_FRAMES  = FPS * ANIM_DURATION

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Create Figure & Axes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

fig, ax = plt.subplots(figsize=(6, 6))
fig.patch.set_facecolor('lightblue')
ax.set_facecolor('lightblue')
ax.set_aspect('equal')
ax.set_xlim(-1.2, 1.4)
ax.set_ylim(-1.2, 1.2)
ax.axis('off')  # Hide axes

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Static Watch Elements: Bezel, Dial, Indices, Crown & Lugs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 3.1 Outer bezel (thick ring)
outer_bezel = Circle(CENTER, radius=R_BEZEL,
                     facecolor='white', edgecolor='black', linewidth=5)
ax.add_patch(outer_bezel)

# 3.2 Inner dial
dial = Circle(CENTER, radius=R_DIAL,
              facecolor='#f5f5f5', edgecolor='grey', linewidth=1.5)
ax.add_patch(dial)

# 3.3 Crown at 3 o’clock
crown_width  = 0.08
crown_height = 0.15
crown_corner = (R_BEZEL + 0.005, -crown_height/2)
crown = Rectangle(crown_corner, crown_width, crown_height,
                  facecolor='silver', edgecolor='dimgray', linewidth=1)
ax.add_patch(crown)

# 3.4 Lugs (top & bottom)
lug_width  = 0.30
lug_height = 0.05
# Top lug
top_lug = Rectangle((-lug_width/2, R_BEZEL + 0.005),
                    lug_width, lug_height,
                    facecolor='silver', edgecolor='dimgray', linewidth=1)
ax.add_patch(top_lug)
# Bottom lug
bottom_lug = Rectangle((-lug_width/2, -R_BEZEL - lug_height - 0.005),
                       lug_width, lug_height,
                       facecolor='silver', edgecolor='dimgray', linewidth=1)
ax.add_patch(bottom_lug)

# 3.5 Hour indices (12 ticks around the dial)
for h in range(12):
    angle_deg = 90 - h * 30  # 12 o’clock at 90°, 3 o’clock at 0°, 6 o’clock at -90°, etc.

    # Cardinal hours (0, 3, 6, 9) get a longer, thicker tick
    if h % 3 == 0:
        length = TICK_LONG
        width  = TICK_WIDTH * 1.4
    else:
        length = TICK_SHORT
        width  = TICK_WIDTH

    x_outer, y_outer = polar_to_cartesian(R_DIAL - 0.02, angle_deg)
    x_inner, y_inner = polar_to_cartesian(R_DIAL - 0.02 - length, angle_deg)

    ax.plot(
        [x_inner, x_outer], [y_inner, y_outer],
        color='black', linewidth=width, solid_capstyle='round'
    )

roman_labels = ["XII", "I", "II", "III", "IIII", "V", 
                "VI", "VII", "VIII", "IX", "X", "XI"]

R_NUMERAL = R_DIAL - 0.15

box_h = 0.5
box_w = 0.1

for h, label in enumerate(roman_labels):
    angle = 90 - h * 30
    x_text, y_text = polar_to_cartesian(R_NUMERAL, angle)
    if label == "XII":
        continue
    if label == "III":
        lower_left = (x_text- box_w/2, y_text - box_h/2)
        ax.text(
            x_text, y_text,
            "25",
            ha="center", va="center",
            fontsize=14, fontweight="bold",
            color="darkgreen",
            zorder=5,
            bbox=dict(
            boxstyle="round,pad=0.2",
            facecolor="white",
            edgecolor="black",
            linewidth=1.2,
        )
        )
        
        continue 
    ax.text(
        x_text, y_text,
        label,
        ha='center', va='center',
        fontsize=18, fontweight='bold',
        fontfamily='Serif',
        color='darkgreen',
        zorder=4
    )
    
pil_img = Image.open("rolex_crown.png").convert("RGBA")
data = np.array(pil_img)  # shape = H×W×4, dtype=uint8

# 2) Build a mask of “white” pixels (you can tweak the threshold)
white_mask = np.all(data[:, :, :3] > 240, axis=2)

# 3) Zero out their alpha
data[white_mask, 3] = 0

# 4) Normalize to floats 0…1
logo_arr = data.astype(float) / 255.0

# …then wrap as you already do:
logo_image = OffsetImage(logo_arr, zoom=0.07)
logo_ab = AnnotationBbox(logo_image, (0, R_BEZEL - 0.3),
                         frameon=False, box_alignment=(0.5,0.5), zorder=5)
ax.add_artist(logo_ab)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Create “Dynamic” Artists for Hands & Text (to be updated each frame)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 4.1 Watch hands (Line2D objects) – initially empty
(hour_line,)   = ax.plot([], [], color='black',
                         linewidth=HOUR_HAND_WIDTH * 100,
                         solid_capstyle='round', zorder=5)
(minute_line,) = ax.plot([], [], color='black',
                         linewidth=MINUTE_HAND_WIDTH * 100,
                         solid_capstyle='round', zorder=6)
(second_line,) = ax.plot([], [], color='red',
                         linewidth=SECOND_HAND_WIDTH * 100,
                         solid_capstyle='round', zorder=7)

# 4.2 Center pinion (small black circle)
center_circle = Circle(CENTER, radius=0.03, facecolor='black', edgecolor='none', zorder=8)
ax.add_patch(center_circle)



# 4.3 “Happy Birthday” Text (starts transparent, fades in & drifts up)
birthday_text = ax.text(
    0, -1.0, "", 
    ha='center', va='center',
    fontsize=20, weight='bold', color='darkblue',
    alpha=0.0, zorder=9
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Animation Update Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_animation():

    hour_line.set_data([], [])
    minute_line.set_data([], [])
    second_line.set_data([], [])
    birthday_text.set_text("")     # no text initially
    birthday_text.set_alpha(0.0)   # fully transparent
    return hour_line, minute_line, second_line, birthday_text

def update_frame(frame):

    # ─── A) Compute elapsed time since start (in seconds) ────────────────────────
    elapsed_seconds = frame / FPS
    total_seconds = START_HOUR * 3600 + START_MINUTE * 60 + START_SECOND + elapsed_seconds

    # Break total_seconds into hours, minutes, seconds
    current_h = (total_seconds % 43200) // 3600       # hour in [0..11]
    rem = total_seconds % 3600
    current_m = rem // 60
    current_s = rem % 60

    # ─── B) Compute each hand’s angle (12 o’clock = 90° clockwise) ───────────────
    hour_angle =  90 - (current_h * 30 + (current_m / 60) * 30)
    minute_angle = 90 - (current_m * 6 + (current_s / 60) * 6)
    second_angle = 90 - (current_s * 6)

    # ─── C) Convert angles → (x, y) endpoints & update hand lines ───────────────
    hx, hy = polar_to_cartesian(HOUR_HAND_LENGTH * R_DIAL, hour_angle)
    hour_line.set_data([0, hx], [0, hy])

    mx, my = polar_to_cartesian(MINUTE_HAND_LENGTH * R_DIAL, minute_angle)
    minute_line.set_data([0, mx], [0, my])

    sx, sy = polar_to_cartesian(SECOND_HAND_LENGTH * R_DIAL, second_angle)
    second_line.set_data([0, sx], [0, sy])

    # ─── D) Fade‐in & Drift “Happy Birthday” Text ─────────────────────────────────
    fade_start_frame = FPS * 1   # 1 second into the animation
    fade_end_frame   = FPS * 3   # fully opaque by 3 seconds

    if frame < fade_start_frame:
        alpha = 0.0
        y_text = -1.0
    elif frame <= fade_end_frame:
        # Linear interpolation from 0→1 (alpha), -1.0→-0.5 (vertical drift)
        t = (frame - fade_start_frame) / (fade_end_frame - fade_start_frame)
        alpha  = t
        y_text = -1.0 + 0.5 * t
    else:
        alpha  = 1.0
        y_text  = -0.5
  ############# Change the message here ##################
    birthday_text.set_text(" Message ")
  
    birthday_text.set_alpha(alpha)
    birthday_text.set_position((0, y_text))

    return hour_line, minute_line, second_line, birthday_text

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Launch the Animation (blit=False to avoid residual artifacts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

anim = animation.FuncAnimation(
    fig,
    update_frame,
    init_func=init_animation,
    frames=TOTAL_FRAMES,
    interval=1000 / FPS,   # milliseconds between frames
    blit=False             # redraw entire canvas each frame
)

mp.rcParams['animation.ffmpeg_path'] = '/opt/homebrew/bin/ffmpeg' # Change According to ffmpeg path 

writer = FFMpegWriter(fps=FPS, metadata=dict(artist='you'), bitrate=1800)
anim.save(
    "/Users/"YOUR_FILEPATH"/Desktop/birthday_watch.mp4",
    writer=writer,
    dpi=150
)

plt.show()
