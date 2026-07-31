"""Robust summary statistics, stdlib only.

Vibration artefacts are heavy-tailed: one bump of the bench, one cable
tug, one door slamming in the lab, and a mean/SD pair is ruined while a
median/MAD pair barely moves.  Every summary this package reports comes
in both flavours so a condition where they *disagree* is visible rather
than silently averaged away -- disagreement is itself the finding
("something bumped the bench during these runs").

Pure stdlib on purpose: the host may well be the Pi Zero 2 W driving the
rig, where a numpy/pandas/scipy stack is a nuisance to install and a
memory problem to run.  Sample sizes here are tens to thousands, so the
O(n log n) sorts cost nothing.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Sequence

#: MAD -> sigma scale factor for a normal distribution (1 / Phi^-1(3/4)).
MAD_TO_SIGMA = 1.4826


def _clean(values: Iterable[float]) -> List[float]:
    """Drop NaN/inf, which otherwise poison every downstream sort."""
    return [float(v) for v in values
            if v is not None and math.isfinite(float(v))]


def mean(values: Sequence[float]) -> Optional[float]:
    vals = _clean(values)
    return sum(vals) / len(vals) if vals else None


def stdev(values: Sequence[float]) -> Optional[float]:
    """Sample standard deviation (n-1), or ``None`` for n < 2."""
    vals = _clean(values)
    if len(vals) < 2:
        return None
    mu = sum(vals) / len(vals)
    return math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))


def median(values: Sequence[float]) -> Optional[float]:
    vals = sorted(_clean(values))
    if not vals:
        return None
    mid = len(vals) // 2
    if len(vals) % 2:
        return vals[mid]
    return 0.5 * (vals[mid - 1] + vals[mid])


def mad(values: Sequence[float], scale: bool = True) -> Optional[float]:
    """Median absolute deviation, scaled to a sigma estimate by default."""
    vals = _clean(values)
    if len(vals) < 2:
        return None
    med = median(vals)
    spread = median([abs(v - med) for v in vals])
    if spread is None:
        return None
    return spread * MAD_TO_SIGMA if scale else spread


def quantile(values: Sequence[float], q: float) -> Optional[float]:
    """Linear-interpolated quantile (the ``numpy.percentile`` default)."""
    vals = sorted(_clean(values))
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * min(max(q, 0.0), 1.0)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def iqr(values: Sequence[float]) -> Optional[float]:
    lo, hi = quantile(values, 0.25), quantile(values, 0.75)
    return None if lo is None or hi is None else hi - lo


def peak_to_peak(values: Sequence[float]) -> Optional[float]:
    vals = _clean(values)
    return max(vals) - min(vals) if vals else None


def sigma_rel_se(n: int) -> Optional[float]:
    """Relative standard error of an SD estimate from ``n`` samples.

    ``SE(sigma) ~= sigma / sqrt(2(n-1))``.  Reported next to every sigma
    so a tight-looking noise floor built on n=4 is not mistaken for a
    measured one: n=20 pins sigma to about +/-16 %, n=5 only to +/-35 %.
    """
    if n < 2:
        return None
    return 1.0 / math.sqrt(2.0 * (n - 1))


def outlier_count(values: Sequence[float], k: float = 3.5) -> int:
    """Count points more than ``k`` robust sigmas from the median.

    Uses MAD rather than SD so the outliers don't inflate the threshold
    that is supposed to catch them.
    """
    vals = _clean(values)
    if len(vals) < 3:
        return 0
    med = median(vals)
    sigma = mad(vals)
    if not sigma:
        return 0
    return sum(1 for v in vals if abs(v - med) > k * sigma)


@dataclass
class Summary:
    """Classical and robust location/scale for one set of replicates."""

    n: int
    mean: Optional[float] = None
    sd: Optional[float] = None
    median: Optional[float] = None
    mad: Optional[float] = None
    iqr: Optional[float] = None
    p05: Optional[float] = None
    p95: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    sigma_rel_se: Optional[float] = None
    n_outliers: int = 0

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def robust_sigma(self) -> Optional[float]:
        """Preferred scale estimate: MAD-based, falling back to SD."""
        return self.mad if self.mad is not None else self.sd


def summarize(values: Sequence[float]) -> Summary:
    vals = _clean(values)
    if not vals:
        return Summary(n=0)
    return Summary(
        n=len(vals),
        mean=mean(vals),
        sd=stdev(vals),
        median=median(vals),
        mad=mad(vals),
        iqr=iqr(vals),
        p05=quantile(vals, 0.05),
        p95=quantile(vals, 0.95),
        min=min(vals),
        max=max(vals),
        sigma_rel_se=sigma_rel_se(len(vals)),
        n_outliers=outlier_count(vals),
    )
