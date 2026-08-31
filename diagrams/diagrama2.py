import matplotlib.pyplot as plt
import matplotlib.patches as patches

# G(s) = 1 / (RCs + 1) — coeficientes simbólicos; apenas diagramas de blocos.

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.suptitle(r"Diagramas de Blocos para $G(s) = \frac{1}{RCs + 1}$", fontsize=16)

# --- Malha aberta ---
ax1.set_title("Diagrama de Blocos da Função de Transferência Fornecida")
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 5)
ax1.set_aspect("equal", adjustable="box")
ax1.axis("off")

block_width, block_height = 2.5, 1.5
block_x, block_y = 3.5, 1.75

ax1.add_patch(
    patches.FancyBboxPatch(
        (block_x, block_y), block_width, block_height,
        boxstyle="round,pad=0.3", fc="lightblue", ec="black", lw=2,
    )
)
ax1.text(
    block_x + block_width / 2, block_y + block_height / 2,
    r"$G(s) = \frac{1}{RCs + 1}$", ha="center", va="center", fontsize=14,
)

mid_y = block_y + block_height / 2
ax1.add_patch(patches.FancyArrowPatch(
    (1, mid_y), (block_x, mid_y),
    arrowstyle="-|>", mutation_scale=20, lw=2, color="black",
))
ax1.text(1.5, mid_y + 0.3, r"$U(s)$", ha="center", va="bottom", fontsize=12)

ax1.add_patch(patches.FancyArrowPatch(
    (block_x + block_width, mid_y), (9, mid_y),
    arrowstyle="-|>", mutation_scale=20, lw=2, color="black",
))
ax1.text(8.5, mid_y + 0.3, r"$Y(s)$", ha="center", va="bottom", fontsize=12)

# --- Malha fechada com realimentação unitária ---
ax2.set_title("Diagrama de Blocos Equivalente com Realimentação Unitária (H(s)=1)")
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 5)
ax2.set_aspect("equal", adjustable="box")
ax2.axis("off")

center_y = 2.5
summator_x = 1.5
summator_radius = 0.4
block_g_x = 4.5

ax2.add_patch(patches.Circle(
    (summator_x, center_y), summator_radius,
    fc="white", ec="black", lw=2, zorder=5,
))
ax2.text(summator_x - summator_radius * 0.7, center_y, "+", ha="center", va="center", fontsize=16)
ax2.text(summator_x, center_y - summator_radius * 0.7, "-", ha="center", va="center", fontsize=16)

ax2.add_patch(patches.FancyBboxPatch(
    (block_g_x, center_y - block_height / 2), block_width, block_height,
    boxstyle="round,pad=0.3", fc="lightblue", ec="black", lw=2,
))
ax2.text(
    block_g_x + block_width / 2, center_y,
    r"$G(s) = \frac{1}{RCs + 1}$", ha="center", va="center", fontsize=14,
)

ax2.add_patch(patches.FancyArrowPatch(
    (0.5, center_y), (summator_x - summator_radius, center_y),
    arrowstyle="-|>", mutation_scale=20, lw=2, color="black",
))
ax2.text(0.7, center_y + 0.3, r"$R(s)$", ha="center", va="bottom", fontsize=12)

ax2.add_patch(patches.FancyArrowPatch(
    (summator_x + summator_radius, center_y), (block_g_x, center_y),
    arrowstyle="-|>", mutation_scale=20, lw=2, color="black",
))
ax2.text(summator_x + 1.0, center_y + 0.3, r"$E(s)$", ha="center", va="bottom", fontsize=12)

ax2.add_patch(patches.FancyArrowPatch(
    (block_g_x + block_width, center_y), (9, center_y),
    arrowstyle="-|>", mutation_scale=20, lw=2, color="black",
))
ax2.text(8.5, center_y + 0.3, r"$Y(s)$", ha="center", va="bottom", fontsize=12)

# Realimentação ortogonal
fb_right = block_g_x + block_width + 0.5
fb_down = center_y - 1.5
fb_top = center_y - summator_radius

for start, end in [
    ((block_g_x + block_width, center_y), (fb_right, center_y)),
    ((fb_right, center_y), (fb_right, fb_down)),
    ((fb_right, fb_down), (summator_x, fb_down)),
    ((summator_x, fb_down), (summator_x, fb_top)),
]:
    style = "-|>" if end == (summator_x, fb_top) else "-"
    ax2.add_patch(patches.FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=20, lw=2, color="black",
    ))

ax2.text(fb_right + 0.1, fb_down - 0.3, r"$Y(s)$", ha="left", va="top", fontsize=12)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig("diagrama_blocos.png", dpi=150, bbox_inches="tight")
print("Diagrama salvo em 'diagrama_blocos.png'.")
