# 12 · J2 secular drift rates

The whole simulation rests on one simplification: the orbit is a **fixed
Keplerian ellipse**. Each time step propagates the spacecraft along the *same*
ellipse - the orbit plane, the shape, and the apsides never move. This chapter
puts a **number** on how good that assumption is, instead of asserting it.

The thing that would invalidate it is Earth's **oblateness** - the planet is not
a perfect sphere, and its equatorial bulge is captured by the second zonal
harmonic **J2** (≈ 1.083 × 10⁻³, framework `constants.py`). J2 is far larger
than every other gravitational perturbation, so if J2 drift is negligible over
our window, the fixed-orbit assumption is safe.

## What J2 does

J2 does not change the orbit's *size* (`a`) or *shape* (`e`) on average, but it
makes three angular elements drift **secularly** - i.e. steadily, never
averaging back out (framework Sec. 3, Eq. 9):

```
RAAN:          Ω̇ = -3/2 · n · J2 · (Rₑ/p)² · cos i
arg. perigee:  ω̇ =  3/4 · n · J2 · (Rₑ/p)² · (5 cos²i − 1)
mean anomaly:  Ṁ =  3/4 · n · J2 · (Rₑ/p)² · (3 cos²i − 1) · √(1−e²)
```

with the semi-latus rectum `p = a(1 − e²)` and mean motion `n = √(µ/a³)`.

* **Ω̇** (nodal regression) rotates the whole orbit plane about Earth's axis.
* **ω̇** (apsidal precession) rotates the ellipse within its plane - i.e. moves
  where apogee sits.
* **Ṁ** is a small correction to the along-track timing.

## The critical inclination - why Molniya flies at 63.4°

The apsidal rate carries the factor `(5 cos²i − 1)`, which is **zero** when

```
cos²i = 1/5   ⟹   i = arccos(1/√5) ≈ 63.4349°
```

This is the **critical inclination**. At it, ω̇ = 0: the argument of perigee
stops drifting and apogee stays **frozen** over the same hemisphere. That is the
entire reason a Molniya orbit is flown at 63.4° - so its long, slow apogee dwell
keeps hanging over the northern latitudes it serves. LunaLink inherits exactly
this design choice.

## The numbers for LunaLink

Computed by `orbit.j2_secular_rates(...)` for the Molniya orbit
(`a = 24 628 km`, `e = 0.7207`, `i = 63.4°`):

| Element | Secular rate | Drift over the ~36 h run |
|---|---|---|
| RAAN (Ω) | **−0.171 °/day** | −0.26° |
| Arg. perigee (ω) | **+0.0005 °/day** | +0.0007° |
| Mean anomaly (extra) | −0.053 °/day | - |

Two things to read off this:

1. **Apogee is frozen.** ω̇ ≈ 0.0005 °/day - three orders of magnitude smaller
   than the nodal rate - because 63.4° sits essentially *on* the critical
   inclination. Over the whole simulation the apsides move by **0.0007°**. The
   "apogee stays in the north" claim is now quantified.
2. **The fixed-orbit assumption is safe.** The largest drift, RAAN, is only
   **0.26°** over the entire 36 h window. Attitude dynamics evolve on
   minute-to-hour timescales against an orbit plane that moves a quarter of a
   degree - completely negligible for ADCS purposes. Actually *propagating* J2
   over this window would change nothing we plot, so we don't; we just report
   the rates as the justification.

## Cross-checks

* **Critical inclination** lands at 63.4349° (machine-exact), and feeding the
  *exact* critical inclination into `j2_secular_rates` returns ω̇ = 7 × 10⁻¹⁷
  °/day - zero to floating-point precision.
* **Textbook LEO** (a = 7000 km, e = 0, i = 51.6°, the ISS band) returns
  Ω̇ ≈ −4.5 °/day and ω̇ ≈ +3.3 °/day - the correct sign and order of magnitude
  for the well-known ISS nodal regression of roughly −5 °/day. The formula is
  therefore validated against an independent regime, not just LunaLink's.

## Where it lives in the code

| Piece | Location |
|---|---|
| Rate formulas + critical inclination | `simulation/physics/orbit/j2.py` |
| Drift accumulated over a window | `orbit.drift_over_window(...)` |
| Attached to each run's result (`result["j2_secular"]`) | `simulation/simulator.py` |
| Printed in the headless summary | `main_simulation.py` |

## Cross-check vs the framework

| Framework concept | Our implementation |
|---|---|
| J2 secular rates (Eq. 9) | `j2_secular_rates` - all three angular elements |
| Critical inclination (63.4° Molniya rationale) | `CRITICAL_INCLINATION_DEG`, `near_critical` flag |
| "Treat the orbit as fixed Keplerian" | Justified numerically: ≤0.26° drift over the run |
