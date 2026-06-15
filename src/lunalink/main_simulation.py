"""Headless ADCS simulation entry point.

Runs the detumbling + sun-pointing simulation over >= 3 orbits and writes all
result plots to ``output/`` without launching the GUI (required by the brief:
"main_simulation.py - produces all plots without GUI. Must run headless.").

Usage:
    python -m lunalink.main_simulation
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt

from .simulation.adcs import simulate, ADCSParams, default_params


def run(output_dir: str = "output", params: ADCSParams = None) -> dict:
    params = params or default_params(mode="full")
    result = simulate(params)

    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    t = result["t_h"]

    # 1. Angular velocity (detumbling)
    fig, ax = plt.subplots(figsize=(8, 4))
    for i, name in enumerate("xyz"):
        ax.plot(t, result["omega_deg_s"][:, i], label=f"ω{name}", linewidth=0.9)
    ax.plot(t, result["omega_mag_deg_s"], "k", label="|ω|", linewidth=1.8)
    if result.get("t_acquire_h") is not None:
        ax.axvline(result["t_acquire_h"], color="0.6", linestyle="--", label="acquired")
    ax.set(xlabel="Time [h]", ylabel="Angular velocity [°/s]",
           title="Detumbling convergence")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "angular_velocity.png", dpi=130); plt.close(fig)

    # 2. Attitude error
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["attitude_error_deg"], color="tab:orange")
    ax.set(xlabel="Time [h]", ylabel="Pointing error [°]",
           title="Sun-pointing attitude error")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "attitude_error.png", dpi=130); plt.close(fig)

    # 3. Reaction-wheel momentum
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["wheel_momentum_mag_nms"], color="tab:green")
    ax.axhline(0.8 * params.rw_max_momentum_nms, color="r", linestyle=":",
               label="desaturation level")
    ax.set(xlabel="Time [h]", ylabel="Wheel momentum [N·m·s]",
           title="Reaction-wheel momentum (desaturation saw-tooth)")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "rw_momentum.png", dpi=130); plt.close(fig)

    # 4. Disturbance torque breakdown
    fig, ax = plt.subplots(figsize=(8, 4))
    for key, label in [("T_gg_nm", "gravity gradient"), ("T_srp_nm", "solar pressure"),
                       ("T_mag_nm", "magnetic"), ("T_aero_nm", "aerodynamic")]:
        ax.semilogy(t, result[key], linewidth=1.0, label=label)
    ax.semilogy(t, result["disturbance_nm"], "k", linewidth=1.8, label="total")
    ax.set(xlabel="Time [h]", ylabel="Disturbance torque [N·m]",
           title="Disturbance torque vs orbit position")
    ax.legend(); ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(out / "disturbance_torque.png", dpi=130); plt.close(fig)

    # 5. Angular momentum sanity check
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, result["angular_momentum_nms"], color="tab:purple")
    ax.set(xlabel="Time [h]", ylabel="|H| [N·m·s]",
           title="Total angular momentum (integrator check)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out / "angular_momentum.png", dpi=130); plt.close(fig)

    print("ADCS simulation complete.")
    print(f"  Detumble acquisition : {result['t_acquire_h']:.2f} h")
    print(f"  Final |ω|            : {result['omega_mag_deg_s'][-1]:.4f} °/s")
    print(f"  Final pointing error : {result['attitude_error_deg'][-1]:.3f} °")
    print(f"  Peak wheel momentum  : {result['wheel_momentum_mag_nms'].max():.2f} N·m·s")
    print(f"  Plots written to     : {out.resolve()}")
    return result


if __name__ == "__main__":
    run()
