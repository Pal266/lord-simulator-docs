"""
Flow-routing and erosion kernels for a planar regional grid (square cells, no wrap-around).
Imported by regional_model.py; does nothing when run on its own.
"""
import heapq, math
import numpy as np
from numba import njit

DI = np.array([1, 1, 0, -1, -1, -1, 0, 1])
DJ = np.array([0, -1, -1, -1, 0, 1, 1, 1])
DL = np.array([1.0, math.sqrt(2), 1.0, math.sqrt(2), 1.0, math.sqrt(2), 1.0, math.sqrt(2)])


@njit(cache=True)
def priority_flood(z, is_sink, eps):
    """Depression filling (Barnes et al. 2014). Sinks and the grid border drain out."""
    H, W = z.shape
    f = z.copy()
    done = np.zeros((H, W), np.bool_)
    heap = [(0.0, 0)]
    heap.pop()
    for j in range(H):
        for i in range(W):
            if is_sink[j, i] or j == 0 or i == 0 or j == H - 1 or i == W - 1:
                done[j, i] = True
                heapq.heappush(heap, (f[j, i], j * W + i))
    while len(heap) > 0:
        h, k = heapq.heappop(heap)
        j = k // W; i = k % W
        for d in range(8):
            jn = j + DJ[d]; inn = i + DI[d]
            if jn < 0 or jn >= H or inn < 0 or inn >= W or done[jn, inn]:
                continue
            done[jn, inn] = True
            if f[jn, inn] <= f[j, i] + eps:
                f[jn, inn] = f[j, i] + eps
            heapq.heappush(heap, (f[jn, inn], jn * W + inn))
    return f


@njit(cache=True)
def receivers(f, is_sink, dx):
    H, W = f.shape
    rec = np.empty(H * W, np.int64)
    dist = np.full(H * W, dx)
    for j in range(H):
        for i in range(W):
            k = j * W + i
            rec[k] = k
            if is_sink[j, i]:
                continue
            best = 0.0
            for d in range(8):
                jn = j + DJ[d]; inn = i + DI[d]
                if jn < 0 or jn >= H or inn < 0 or inn >= W:
                    continue
                L = DL[d] * dx
                s = (f[j, i] - f[jn, inn]) / L
                if s > best:
                    best = s; rec[k] = jn * W + inn; dist[k] = L
    return rec, dist


@njit(cache=True)
def accumulate(order_desc, rec, w):
    acc = w.copy()
    for k in order_desc:
        r = rec[k]
        if r != k:
            acc[r] += acc[k]
    return acc


@njit(cache=True)
def stream_power(h, order_asc, rec, dist, Q, K, m, dt, fixed):
    for k in order_asc:
        r = rec[k]
        if r == k or fixed[k]:
            continue
        F = K * dt * Q[k] ** m / dist[k]
        hn = (h[k] + F * h[r]) / (1 + F)
        if hn < h[k]:
            h[k] = hn
    return h


def route(z, sinks, dx):
    f = priority_flood(z, sinks, 1e-4)
    rec, dist = receivers(f, sinks, dx)
    oa = np.argsort(f, axis=None, kind="stable")
    return f, rec, dist, oa, oa[::-1].copy()


def diffuse(z, D, dt, dx, fixed, steps):
    """Explicit linear hillslope diffusion dz/dt = D * laplacian(z) (fixed cells untouched)."""
    sub = max(1, int(math.ceil(4 * D * dt / dx ** 2 / 0.9)))
    h = dt / sub
    for _ in range(steps * sub):
        lap = np.zeros_like(z)
        lap[1:-1, 1:-1] = (z[2:, 1:-1] + z[:-2, 1:-1] + z[1:-1, 2:] + z[1:-1, :-2] - 4 * z[1:-1, 1:-1]) / dx ** 2
        z = np.where(fixed, z, z + D * h * lap)
    return z
