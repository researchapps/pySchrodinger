# Helpler functions to Schodinger, derived from animate_schrodinger and
# intended to be provided to gridtest.

import numpy as np

######################################################################
# Helper functions for gaussian wave-packets
def gauss_x(x, a, x0, k0):
    """
    a gaussian wave packet of width a, centered at x0, with momentum k0
    """
    return ((a * np.sqrt(np.pi)) ** (-0.5)
            * np.exp(-0.5 * ((x - x0) * 1. / a) ** 2 + 1j * x * k0))


def gauss_k(k, a, x0, k0):
    """
    analytical fourier transform of gauss_x(x), above
    """
    return ((a / np.sqrt(np.pi)) ** 0.5
            * np.exp(-0.5 * (a * (k - k0)) ** 2 - 1j * (k - k0) * x0))


######################################################################
# Utility functions for running the animation
def theta(x):
    """
    theta function :
      returns 0 if x<=0, and 1 if x>0
    """
    x = np.asarray(x)
    y = np.zeros(x.shape)
    y[x > 0] = 1.0
    return y


def square_barrier(x, width, height):
    return height * (theta(x) - theta(x - width))

######################################################################
# Generate arguments for Schrodinger

def generate_psi_x0(N = 2 ** 11, dx = 0.1, V0 = 1.5, m=1.9):
    """generate the ps1_x0 variable for gridtest
    """
    # specify constants
    hbar = 1.0   # planck's constant

    # specify initial momentum and quantities derived from it
    p0 = np.sqrt(2 * m * 0.2 * V0)
    dp2 = p0 * p0 * 1. / 80
    d = hbar / np.sqrt(2 * dp2)
    x = generate_x(N, dx)

    L = hbar / np.sqrt(2 * m * V0)
    a = 3 * L
    x0 = -60 * L
    k0 = p0 / hbar

    # this is psi_x0
    return gauss_x(x, d, x0, k0)


def generate_x(N = 2 ** 11, dx = 0.1):
    """specify initial momentum and quantities derived from it
    """
    return dx * (np.arange(N) - 0.5 * N)

def generate_V_x(N = 2 ** 11, dx = 0.1, V0 = 1.5, m=1.9):
    """generate the ps1_x0 variable for gridtest
       m is particle's mass
    """
    # specify constants
    hbar = 1.0   # planck's constant
    x = generate_x(N, dx)

    L = hbar / np.sqrt(2 * m * V0)
    a = 3 * L

    V_x = square_barrier(x, a, V0)
    V_x[x < -98] = 1E6
    V_x[x > 98] = 1E6
    return V_x
