from decimal import Decimal, getcontext
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math

# Set the precision for Decimal calculations
getcontext().prec = 100

# Constants
window_size = 12
pic_size = window_size * 6
dx = window_size / pic_size
pic_shape = (pic_size, pic_size)


# Generate thin lens operator for a range of k values with a 180-degree phase shift
# def generate_lens(num_terms):
#     # Constants for the Chudnovsky algorithm
#     sum_series = Decimal(0)
#     sign = Decimal(1)
#     lens = np.zeros(pic_shape, dtype=np.complex64)
#     center_x, center_y = pic_size / 2, pic_size / 2
#     K = Decimal(640320)
#
#     for k in range(num_terms):
#         # Compute factorial terms
#         num = Decimal(math.factorial(6 * k)) * (545140134 * k + 13591409)
#         K_pow = K ** (3 * k + Decimal(1.5))  # Use Decimal for power operation
#         den = (Decimal(math.factorial(3 * k)) *
#                (Decimal(math.factorial(k)) ** 3) *
#                K_pow)
#         sum_series += sign * num / den
#         sign = -sign  # Flip sign for next term
#
#         # Compute pi using the partial sum up to this point
#         # pi_value_12 = float(1 / sum_series)  # Convert to float for compatibility with numpy
#
#         for y in range(lens.shape[0]):
#             for x in range(lens.shape[1]):
#                 theta=float(0)
#                 r = np.sqrt((dx * (x - center_x)) ** 2 + (dx * (y - center_y)) ** 2)
#                 theta += np.arctan2(y - center_y, x - center_x) + float(sum_series)  # Adding calculated pi value
#                 phase = r ** 2 * np.exp(1j * theta)
#                 lens[y, x] = np.exp(k * (-1j) * phase / (window_size ** 2))
#
#     return lens

def generate_lens(num_terms):
    # Constants for the Chudnovsky algorithm
    sum_series = Decimal(0)
    sign = Decimal(1)
    lens = np.zeros(pic_shape, dtype=np.complex64)
    center_x, center_y = pic_size / 2, pic_size / 2
    K = Decimal(640320)
    theta = float(0)
    for k in range(num_terms):
        # Compute factorial terms
        num = Decimal(math.factorial(6 * k)) * (545140134 * k + 13591409)
        K_pow = K ** (3 * k + Decimal(1.5))  # Use Decimal for power operation
        den = (Decimal(math.factorial(3 * k)) *
               (Decimal(math.factorial(k)) ** 3) *
               K_pow)
        sum_series += sign * num / den
        sign = -sign  # Flip sign for next term

        # Compute pi using the partial sum up to this point
        # pi_value_12 = float(1 / sum_series)  # Convert to float for compatibility with numpy
        for y in range(lens.shape[0]):
            for x in range(lens.shape[1]):
                r = np.sqrt((dx * (x - center_x)) ** 2 + (dx * (y - center_y)) ** 2)
                # phase = r ** 2 * np.exp(1j * theta)
                phase = r * np.exp(1j * theta)
                lens[y, x] = np.exp(k * (-1j) * phase / (window_size ** 2))
        theta = theta+ np.arctan2(y - center_y, x - center_x) + float(1 / (12 * sum_series))  # Adding calculated pi value
    return lens

# Initialize plot
fig, ax = plt.subplots(figsize=(3, 3))
fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
ax.axis('off')

lens = generate_lens(40)
im = ax.imshow(np.real(lens), animated=True, cmap='spring', vmin=-1, vmax=1)

# Update function for animation
def updatefig(k):
    lens = generate_lens(k)
    im.set_array(np.real(lens))
    return im,

# Create animation
ani = animation.FuncAnimation(fig, updatefig, frames=range(1,100), interval=12, blit=True)

# Save the animation
gif_path = '/Users/mac/Desktop/animationlogo_pi.gif'
ani.save(gif_path, writer='imagemagick', fps=5)
