"""Headless ADCS simulation entry point.

Runs the two scenarios required by the project brief, each over 4 full orbits
(about 43 hours, satisfying "at least 3 full orbits / at least 36 hours"):

    1. B-dot magnetic detumbling from a 10 deg/s tumble
    2. Quaternion-PD sun pointing with reaction wheels and desaturation

and writes all result plots to ``output/`` without launching the GUI
("main_simulation.py: produces all plots without GUI. Must run headless.").

Usage:
    python -m lunalink.main_simulation
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt

from .simulation.parameters import ADCSParams, default_params
from .simulation.simulator import simulate


def run(output_dir: str = "output", params: ADCSParams = None,
        prefix: str = "") -> dict:
    """Simulate one scenario and write its plot set (prefixed PNG files)."""
    params = params or default_params(mode="full")
    result = simulate(params)

    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    t = result["t_h"]

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(out / f"{prefix}{name}.png", dpi=130)
        plt.close(fig)

    # 1. Angular velocity (detumbling)
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, name in enumerate("xyz"):
        ax.plot(t, result["omega_deg_s"][:, i], label=f"ω{name}", linewidth=0.9)
    ax.plot(t, result["omega_mag_deg_s"], "k", label="|ω|", linewidth=1.8)
    if result.get("t_acquire_h") is not None:
        ax.axvline(result["t_acquire_h"], color="0.6", linestyle="--", label="acquired")
    ax.set(xlabel="Time [h]", ylabel="Angular velocity [°/s]",
           title="Body angular velocity")
    ax.legend(); ax.grid(alpha=0.3)
    save(fig, "angular_velocity")

    # 2. Attitude error
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["attitude_error_deg"], color="tab:orange")
    ax.set(xlabel="Time [h]", ylabel="Pointing error [°]",
           title="Sun-pointing attitude error")
    ax.grid(alpha=0.3)
    save(fig, "attitude_error")

    # 3. Reaction-wheel momentum
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["wheel_momentum_mag_nms"], color="tab:green")
    ax.axhline(result.get("desat_trigger_nms",
                          params.desat_trigger_fraction * params.rw_max_momentum_nms),
               color="orange", linestyle=":", label="desaturation trigger")
    ax.axhline(params.rw_max_momentum_nms, color="r", linestyle="--",
               label="per-wheel capacity")
    ax.set(xlabel="Time [h]", ylabel="Wheel momentum [N·m·s]",
           title="Reaction-wheel stored momentum")
    ax.legend(); ax.grid(alpha=0.3)
    save(fig, "rw_momentum")

    # 4. Disturbance torque breakdown
    fig, ax = plt.subplots(figsize=(8, 4))
    for key, label in [("T_gg_nm", "gravity gradient"), ("T_srp_nm", "solar pressure"),
                       ("T_mag_nm", "magnetic"), ("T_aero_nm", "aerodynamic")]:
        ax.semilogy(t, result[key], linewidth=1.0, label=label)
    ax.semilogy(t, result["disturbance_nm"], "k", linewidth=1.8, label="total")
    ax.set(xlabel="Time [h]", ylabel="Disturbance torque [N·m]",
           title="Disturbance torque vs orbit position")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    save(fig, "disturbance_torque")

    # 5. Angular momentum sanity check
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["angular_momentum_nms"], color="tab:purple")
    ax.set(xlabel="Time [h]", ylabel="|H| [N·m·s]",
           title="Total angular momentum (integrator check)")
    ax.grid(alpha=0.3)
    save(fig, "angular_momentum")

    # 6. Momentum budget (disturbance angular-momentum demand)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["dist_momentum_nms"], color="tab:blue")
    ax.set(xlabel="Time [h]", ylabel="|∫T_dist dt| [N·m·s]",
           title="Disturbance momentum demand (wiggle = cyclic, climb = secular)")
    ax.grid(alpha=0.3)
    save(fig, "momentum_budget")

    # 7. Determination: knowledge error vs control error (pointing budget)
    det = result.get("determination")
    if det and "knowledge_error_deg" in result:
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        a1.plot(t, result["knowledge_error_deg"], color="tab:red", linewidth=0.9,
                label="knowledge error (estimate vs truth)")
        a1.plot(t, result["attitude_error_deg"], color="tab:orange", linewidth=0.9,
                label="control error (truth vs command)")
        a1.axhline(det["knowledge_budget_deg"], color="tab:red", linestyle=":",
                   label="knowledge budget 0.01°")
        a1.set(ylabel="Error [°]", title="Pointing budget: knowledge vs control")
        a1.set_yscale("log"); a1.legend(fontsize=8); a1.grid(alpha=0.3, which="both")
        a2.plot(t, result["gyro_bias_error_deg_hr"], color="tab:blue")
        a2.set(xlabel="Time [h]", ylabel="Gyro-bias error [°/hr]",
               title="Gyro-bias estimate convergence")
        a2.grid(alpha=0.3)
        save(fig, "pointing_budget")

    acquire = result.get("t_acquire_h")
    budget = result.get("momentum_budget", {})
    print("ADCS simulation complete.")
    acq_label = "Slew settle" if params.mode == "slew" else "Detumble acquisition"
    print(f"  {acq_label:<20} : {acquire:.2f} h" if acquire is not None
          else f"  {acq_label:<20} : not reached in run")
    print(f"  Final |ω|            : {result['omega_mag_deg_s'][-1]:.4f} °/s")
    print(f"  Final pointing error : {result['attitude_error_deg'][-1]:.3f} °")
    print(f"  Peak wheel momentum  : {result['wheel_momentum_mag_nms'].max():.2f} N·m·s")
    slew = result.get("slew")
    if slew:
        settle = slew.get("settle_time_s")
        print("  Slew (rest-to-rest):")
        print(f"    Commanded angle      : {slew['angle_deg']:.0f}°  (I_axis {slew['inertia_axis_kgm2']:.0f} kg·m²)")
        print(f"    Bang-bang estimate   : {slew['bang_bang_time_s']:.0f} s  (2√(θ/α))")
        print("    Actual settle (<thr) : "
              + (f"{settle:.0f} s" if settle is not None else "not reached"))
        print(f"    Peak wheel momentum  : {slew['peak_wheel_nms']:.2f} N·m·s"
              f" ({slew['peak_momentum_nms']:.2f} ideal)"
              + ("  → MOMENTUM-LIMITED" if slew['momentum_limited'] else ""))
    if budget:
        slew = budget.get("slew_momentum_nms", 0.0)
        slew_angle = budget.get("slew_angle_deg") or 90.0
        driver = "slew" if slew >= budget["cyclic_swing_nms"] else "disturbance"
        print("  Momentum budget:")
        print(f"    Cyclic disturbance swing / orbit (store): ±{budget['cyclic_swing_nms']:.3f} N·m·s")
        print(f"    Slew demand ({slew_angle:.0f} deg):                      {slew:.2f} N·m·s  [{driver}-driven]")
        print(f"    Secular momentum / day (dump):             {budget['secular_per_day_nms']:.3f} N·m·s/day")
        print(f"    -> wheels h_max >= {budget['recommended_wheel_hmax_nms']:.2f} N·m·s,"
              f" dump dipole >= {budget['dump_dipole_am2']:.0f} A·m²")
    print("  Disturbance hierarchy:")
    for e in result.get("disturbance_hierarchy", []):
        print(f"    {e['source']:<18} peak {e['peak_nm']:.2e} N·m  [{e['behaviour']}]")
    j2 = result.get("j2_secular")
    if j2:
        d = j2["drift_over_run"]
        crit = " (≈critical: apogee frozen)" if j2["near_critical"] else ""
        print("  J2 secular drift (justifies fixed-orbit assumption):")
        print(f"    RAAN rate          : {j2['raan_dot_deg_day']:+.4f} °/day"
              f"  → {d['raan_drift_deg']:+.4f}° over {d['window_days']:.2f} d")
        print(f"    Arg-perigee rate   : {j2['argp_dot_deg_day']:+.4f} °/day"
              f"  → {d['argp_drift_deg']:+.4f}° over the run{crit}")
        print(f"    Critical incl.     : {j2['critical_inclination_deg']:.2f}°")
    det = result.get("determination")
    if det:
        ok = "✓" if det["knowledge_rms_deg"] <= det["knowledge_budget_deg"] else "✗"
        print("  Attitude determination (pointing budget):")
        print(f"    Gyro bias learned    : {det['bias_initial_deg_hr']:.2f}"
              f" → {det['bias_final_deg_hr']:.3f} °/hr")
        print(f"    Knowledge error      : RMS {det['knowledge_rms_deg']:.4f}°"
              f"  (budget {det['knowledge_budget_deg']:.2f}°) {ok}")
        print(f"    Control error        : RMS {det['control_rms_deg']:.4f}°"
              f"  (budget {det['control_budget_deg']:.2f}°)")
        print(f"    Total pointing       : {det['pointing_total_deg']:.4f}°"
              f"  (budget {det['total_budget_deg']:.2f}°)")
    print(f"  Plots written to     : {out.resolve()}")
    return result


def main(output_dir: str = "output"):
    """Run the two scenarios required by the brief and write all plots.

    Each scenario covers 4 full orbits (about 43 h), satisfying the
    "at least 3 full orbits / at least 36 hours" requirement.
    """
    print("=" * 62)
    print("Scenario 1/2: B-dot magnetic detumbling (4 orbits)")
    print("=" * 62)
    run(output_dir, default_params(mode="detumble"), prefix="detumble_")
    print()
    print("=" * 62)
    print("Scenario 2/2: quaternion-PD sun pointing with reaction wheels")
    print("=" * 62)
    run(output_dir, default_params(mode="sun_pointing"), prefix="sunpoint_")


if __name__ == "__main__":
    main()
