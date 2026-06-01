### WallLabelling.py
### MIT LICENSE 2024 Marcio Gameiro

import pychomp
import numpy as np

def ramp_system_wall_labelling(gamma, theta, h, f_ramp):
    """Compute wall labelling from a ramp system"""
    # Space dimension
    dim = len(gamma)
    # Get outgoing theta and h
    theta_out, h_out = [], []
    for n in range(dim):
        theta_n, h_n = [], []
        for k in range(dim):
            theta_n.extend(theta[k][n])
            h_n.extend(h[k][n])
        theta_out.append(theta_n)
        h_out.append(h_n)
    # Sort theta and h
    theta_s, h_s = [], []
    for n in range(dim):
        theta_n = theta_out[n]
        h_n = h_out[n]
        sorted_indices = np.argsort(theta_n)
        theta_n_sorted = [theta_n[k] for k in sorted_indices]
        h_n_sorted = [h_n[k] for k in sorted_indices]
        theta_s.append(theta_n_sorted)
        h_s.append(h_n_sorted)
    # Number of thresholds (thetas) in each dimension
    num_thetas = [len(theta_s[n]) for n in range(dim)]

    def cell_wall_label(top_cell):
        """Return wall labelling of a top cell"""
        # Get cell coordinates
        coords = cc.coordinates(top_cell)
        # Get point in the cell where ramp function is constant (theta - h or theta + h for right most cell)
        x_cell = [theta_s[n][k] - h_s[n][k] if k < num_thetas[n] else theta_s[n][k - 1] + h_s[n][k - 1] for n, k in enumerate(coords)]
        # Evaluate the ramp system at x_cell
        f_x_cell = f_ramp(x_cell)
        # Get the theta values at the left walls of cell
        theta_left = [theta_s[n][k - 1] if k > 0 else 0 for n, k in enumerate(coords)]
        # Get the theta values at the right walls of cell (take theta + 10 * h at the right most wall)
        theta_right = [theta_s[n][k] if k < num_thetas[n] else theta_s[n][k - 1] + 10 * h_s[n][k - 1] for n, k in enumerate(coords)]
        # Get values of the ramp system on the left walls
        left_wall_vals = [-gamma[n] * theta_left[n] + f_x_cell[n] for n in range(dim)]
        # Get values of the ramp system on the right walls
        right_wall_vals = [-gamma[n] * theta_right[n] + f_x_cell[n] for n in range(dim)]
        # Make sure the values at the walls are nonzero
        if any(val == 0 for val in left_wall_vals):
            raise ValueError('Ramp system evaluates to zero on left wall.')
        if any(val == 0 for val in right_wall_vals):
            raise ValueError('Ramp system evaluates to zero on right wall.')
        # Get the signs (wall labelling) on the left walls
        left_wall_signs = [-1 if val < 0 else 1 for val in left_wall_vals]
        # Get the signs (wall labelling) on the right walls
        right_wall_signs = [-1 if val < 0 else 1 for val in right_wall_vals]
        # Get bit-wise representation of wall labelling
        wall_label = 0
        for n in range(dim):
            # Set left walls sign
            if left_wall_signs[n] == -1:
                # Set bit (move left)
                wall_label |= (1 << n)
            # Set right walls sign
            if right_wall_signs[n] == 1:
                # Set bit (move right)
                wall_label |= (1 << n + dim)
        return wall_label

    # Create cubical complex
    num_boxes = [k + 1 for k in num_thetas]
    cc = pychomp.CubicalComplex(num_boxes)
    # Get labelling of each top cell
    labelling = []
    for top_cell in cc(dim):
        wall_label = cell_wall_label(top_cell)
        labelling.append(wall_label)
    return labelling, num_thetas
