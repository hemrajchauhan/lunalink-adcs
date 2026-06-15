"""Physics calculations, organised by domain so each block of equations lives
in its own small, commented module that can be cross-checked against the
LunaLink ADCS Mathematical Framework.

    constants      - physical / Earth constants (framework Sec. 1)
    orbit          - Kepler propagation and state vectors (Sec. 3)
    attitude       - quaternion kinematics and pointing (Sec. 4)
    environment    - Sun, eclipse, geomagnetic field, atmosphere (Sec. 7)
    disturbances   - gravity gradient, SRP, magnetic, drag torques (Sec. 6)
    dynamics       - rigid-body Euler equation, mass properties (Sec. 5)
    actuators      - reaction-wheel / magnetorquer sizing (Sec. 8)
    control        - B-dot detumble, PD pointing, desaturation (Sec. 9)
"""
