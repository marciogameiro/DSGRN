### RampFunction.py
### MIT LICENSE 2024 Marcio Gameiro

def linear_function(x, x_vals, y_vals):
    # Equation of line y = m * x + b
    m = (y_vals[1] - y_vals[0]) / (x_vals[1] - x_vals[0])
    b = y_vals[0] - m * x_vals[0]
    return m * x + b

def find_theta_interval(x, theta):
    N = len(theta)
    if x <= theta[0]:
        return -1, 0
    if x >= theta[-1]:
        return N - 1, -1
    for k in range(N):
        if x >= theta[k] and x <= theta[k + 1]:
            return k, k + 1

def ramp_function(x, nu, theta, h):
    # First value if before first endpoint
    if x <= theta[0] - h[0]:
        return nu[0]
    # Last value if after the last endpoint
    if x >= theta[-1] + h[-1]:
        return nu[-1]
    # Case with a single ramp
    if len(theta) == 1:
        k1, k2 = 0, 1
        x_vals = theta[k1] - h[k1], theta[k1] + h[k1]
        y_vals = nu[k1], nu[k2]
        return linear_function(x, x_vals, y_vals)
    # Find theta interval containing x
    k1, k2 = find_theta_interval(x, theta)
    # Consider the edge cases
    N = len(theta)
    if k1 == -1:
        k1, k2 = 0, 1
    if k2 == -1:
        k1, k2 = N - 2, N - 1
    # Check if flat portion of the ramp
    if x >= theta[k1] + h[k1] and x <= theta[k2] - h[k2]:
        return nu[k2]
    # It is a linear function
    if x < theta[k1] + h[k1]:
        x_vals = theta[k1] - h[k1], theta[k1] + h[k1]
        y_vals = nu[k1], nu[k2]
    if x > theta[k2] - h[k2]:
        x_vals = theta[k2] - h[k2], theta[k2] + h[k2]
        y_vals = nu[k2], nu[k2 + 1]
    return linear_function(x, x_vals, y_vals)
