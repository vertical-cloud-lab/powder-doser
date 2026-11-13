"""Yield locus and Mohr-circle analysis shared by the FT4 and ring-shear scenes.

A straight yield locus tau = c + mu * sigma is fitted to the failure points. The unconfined
yield strength sigma_c is the diameter of the Mohr circle through the origin tangent to the
locus; the major principal stress sigma_1 is the right end of the circle through the
pre-shear point tangent to the locus; ffc = sigma_1 / sigma_c, classed after Jenike.
"""
from __future__ import annotations

import math

import numpy as np

from common import C, ramp, style_axes


def fit_locus(sig, tau):
    A = np.c_[np.ones(len(sig)), sig]
    c, mu = np.linalg.lstsq(A, np.asarray(tau, float), rcond=None)[0]
    return float(c), float(mu)


def mohr(c, mu, sp, tp):
    """(sigma_c, x0, R, sigma_1): sigma_c from the circle through 0 tangent to the locus, and the
    steady-flow circle (centre x0, radius R) through the pre-shear point (sp, tp) tangent to it."""
    phi = math.atan(mu)
    sig_c = 2 * c * (1 + math.sin(phi)) / math.cos(phi)
    k = 1 / (1 + mu * mu)
    b = sp + k * mu * c
    disc_ = max(0.0, b * b - k * (sp * sp + tp * tp - k * c * c))
    x0 = (b + math.sqrt(disc_)) / k
    R = math.hypot(sp - x0, tp)
    return sig_c, x0, R, x0 + R


def ffc_class(f):
    return ("not flowing" if f < 1 else "very cohesive" if f < 2 else "cohesive" if f < 4
            else "easy-flowing" if f < 10 else "free-flowing")


def locus_chart(fig, tau_t, sig_sh, tau_f, sp, tp):
    """Yield locus and Mohr circles, revealed progressively over about 3 s (tau_t = time since start)."""
    c, mu = fit_locus(sig_sh, tau_f)
    sig_c, x0, R, s1 = mohr(c, mu, sp, tp)
    f = s1 / sig_c
    ax = fig.add_axes([0.11, 0.17, 0.86, 0.70])
    style_axes(ax, "Yield locus and Mohr circles")
    s_pts = ramp(tau_t, 0.0, 0.5)
    s_line = ramp(tau_t, 0.4, 1.0)
    s_c1 = ramp(tau_t, 0.9, 1.6)
    s_c2 = ramp(tau_t, 1.5, 2.3)
    n_show = int(round(s_pts * len(sig_sh)))
    ax.plot(list(sig_sh)[:n_show], list(tau_f)[:n_show], "o", color=C["orange"], ms=6,
            label="failure (shear) points", zorder=5)
    if s_pts > 0.2:
        ax.plot([sp], [tp], "s", color=C["blue"], ms=6, label="pre-shear point", zorder=5)
    if s_line > 0:
        xl = np.linspace(0, sp * s_line, 50)
        ax.plot(xl, c + mu * xl, color="#222", lw=1.8, label=f"yield locus τ = {c:.2f} + {mu:.2f}σ")
    if s_c1 > 0:
        a = np.linspace(np.pi, np.pi - np.pi * s_c1, 80)
        ax.plot(sig_c / 2 + sig_c / 2 * np.cos(a), sig_c / 2 * np.sin(a), color=C["green"], lw=2.0)
    if s_c2 > 0:
        a = np.linspace(np.pi, np.pi - np.pi * s_c2, 120)
        ax.plot(x0 + R * np.cos(a), R * np.sin(a), color=C["red"], lw=2.0)
    xmax = max(s1 * 1.06, 10)
    if s_c1 >= 1:
        ax.plot([sig_c], [0], "v", color=C["green"], ms=7, clip_on=False, zorder=6)
        ax.text(sig_c + 0.012 * xmax, 0.015 * xmax, "σc", fontsize=9, color=C["green"], ha="left",
                fontweight="bold")
    if s_c2 >= 1:
        ax.plot([s1], [0], "v", color=C["red"], ms=7, clip_on=False, zorder=6)
        ax.text(s1 - 0.012 * xmax, 0.015 * xmax, "σ1", fontsize=9, color=C["red"], ha="right",
                fontweight="bold")
    if tau_t > 2.4:
        ax.text(0.99, 0.97, f"σc = {sig_c:.1f} kPa,  σ1 = {s1:.1f} kPa\nffc = σ1/σc = {f:.1f}: {ffc_class(f)}",
                transform=ax.transAxes, ha="right", va="top", fontsize=9, fontweight="bold", color="#222",
                bbox=dict(boxstyle="round,pad=0.35", fc="#fff6e8", ec="#e07a1f", lw=1))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, xmax * 0.5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("normal stress σ (kPa)")
    ax.set_ylabel("shear stress τ (kPa)")
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)


def jenike_note():
    return "ffc classes (Jenike): <1 not flowing · 1–2 very cohesive · 2–4 cohesive · 4–10 easy-flowing · >10 free-flowing"
