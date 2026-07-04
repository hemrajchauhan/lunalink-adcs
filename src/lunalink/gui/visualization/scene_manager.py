import numpy as np
import pyvista as pv
from PyQt6.QtCore import QTimer

from ...simulation.system import SolarSystem
from ...simulation.objects import Satellite
from ...simulation.physics import orbit
from .transforms import VisualizationTransform
from .camera_manager import CameraManager
from ... import config
from ...config import (
    ANIMATION_FPS, TIME_ACCELERATION, SATELLITE_DISPLAY_SIZE,
    STAR_COUNT, STAR_FIELD_RADIUS,
)


class SceneManager:
    """Owns the 3D scene (planets, moons, satellites, orbit paths, stars) and
    the animation clock. Labels follow their objects; camera, speed, pause,
    freeze and click-to-inspect are all exposed for the GUI."""

    def __init__(self, plotter):
        self.plotter = plotter
        self.camera_manager = CameraManager(plotter)
        self.system = SolarSystem()

        self.sim_time_s = 0.0
        self.time_acceleration = TIME_ACCELERATION

        self.body_actors = {}
        self.satellite_actors = {}
        self.orbit_actors = {}            # name -> (actor, parent_name)
        self.display_radius = {}
        self.child_scale = {}             # name -> metres->units scale for moons/sats
        self.scene_positions = {}
        self._label_poly = None
        self._label_names = []
        self._orbits_visible = True
        self._labels_visible = True

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_tick)

    # =====================================================================
    #  Construction
    # =====================================================================
    def _configure_renderer(self):
        self.plotter.set_background(config.SCENE_BACKGROUND)
        self.plotter.enable_anti_aliasing()
        self.plotter.remove_all_lights()
        sun_light = pv.Light(position=(0, 0, 0), color="white",
                             intensity=config.SUN_LIGHT_INTENSITY)
        sun_light.positional = True
        sun_light.attenuation_values = (1.0, 0.0, 0.0)
        self.plotter.add_light(sun_light)
        self.plotter.add_light(pv.Light(light_type="headlight",
                                        intensity=config.FILL_LIGHT_INTENSITY))
        # Orientation axes with bright, readable labels (dark background fix).
        x_c, y_c, z_c = config.AXIS_COLORS
        try:
            self.plotter.add_axes(
                xlabel="X", ylabel="Y", zlabel="Z",
                x_color=x_c, y_color=y_c, z_color=z_c,
                line_width=3, labels_off=False)
        except TypeError:
            self.plotter.add_axes()

    def _add_starfield(self):
        rng = np.random.default_rng(42)
        directions = rng.normal(size=(STAR_COUNT, 3))
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        cloud = pv.PolyData(directions * STAR_FIELD_RADIUS)
        self.plotter.add_mesh(cloud, color=config.STAR_COLOR,
                              point_size=config.STAR_POINT_SIZE,
                              render_points_as_spheres=True, lighting=False,
                              name="starfield", pickable=False)

    def setup_scene(self):
        self._configure_renderer()
        self._add_starfield()
        self.system.reload()

        # Display sizes and per-child orbit scales must exist before positions.
        for body in self.system.bodies:
            self.display_radius[body.name] = VisualizationTransform.body_display_radius(body.radius_m)
        self._compute_child_scales()
        self._update_positions(self.sim_time_s)

        for body in self.system.bodies:
            self.body_actors[body.name] = self._render_body(body)
        for satellite in self.system.satellites:
            self.satellite_actors[satellite.name] = self._render_satellite(satellite)

        self._render_orbits()
        self._build_labels()
        # Click-to-inspect text overlay intentionally disabled: use the Objects
        # tab (double-click to focus) to inspect an object instead.
        self.focus_on_body("Earth")

    def reload_scene(self):
        was_running = self._timer.isActive()
        self._timer.stop()
        self.plotter.clear()
        self.plotter.remove_all_lights()
        self.body_actors.clear()
        self.satellite_actors.clear()
        self.orbit_actors.clear()
        self.display_radius.clear()
        self.child_scale.clear()
        self.scene_positions.clear()
        self._label_poly = None
        self.setup_scene()
        self.plotter.render()
        if was_running:                 # keep animating after an edit/delete
            self.start_animation()

    # =====================================================================
    #  Positions (scene units)
    # =====================================================================
    def _compute_child_scales(self):
        """One metres->units scale per moon/satellite so each orbit sits at a
        bounded, parent-relative distance (computed once at scene build)."""
        self.child_scale = {}
        for obj in self.system.all_objects():
            if obj.orbit is None or obj.parent is None or obj.parent == "Sun":
                continue
            p_disp = self.display_radius.get(obj.parent, 2.0)
            self.child_scale[obj.name] = VisualizationTransform.child_orbit_scale(
                obj.orbit.semi_major_axis_m, obj.orbit.eccentricity,
                p_disp, isinstance(obj, Satellite))
        self._push_moons_outside_satellites()

    def _push_moons_outside_satellites(self):
        """When a moon and a satellite share a parent, a highly eccentric
        satellite orbit (e.g. a Molniya) can reach farther out than the moon,
        so the two orbit lines cross. Rescale each such moon so its closest
        approach clears the farthest satellite apogee (matches reality: the
        satellite stays well inside the lunar orbit)."""
        parents = {o.parent for o in self.system.all_objects()
                   if o.parent and o.parent != "Sun" and o.orbit is not None}
        for parent in parents:
            children = [o for o in self.system.all_objects()
                        if o.parent == parent and o.orbit is not None]
            sats = [o for o in children if isinstance(o, Satellite)]
            moons = [o for o in children if not isinstance(o, Satellite)]
            if not sats or not moons:
                continue
            max_sat_apogee = max(
                o.orbit.semi_major_axis_m * (1.0 + o.orbit.eccentricity)
                * self.child_scale.get(o.name, 0.0) for o in sats)
            needed = max_sat_apogee * config.MOON_SATELLITE_CLEARANCE
            for moon in moons:
                perigee_m = moon.orbit.semi_major_axis_m * (1.0 - moon.orbit.eccentricity)
                if perigee_m <= 0:
                    continue
                perigee_disp = perigee_m * self.child_scale.get(moon.name, 0.0)
                if perigee_disp < needed:
                    self.child_scale[moon.name] = needed / perigee_m

    def _update_positions(self, time_s):
        world = self.system.compute_positions(time_s)
        self.scene_positions = {}
        for obj in self.system.all_objects():
            self.scene_positions[obj.name] = self._scene_position(obj, world)
        self._world_positions = world

    def _scene_position(self, obj, world):
        if obj.parent is None or obj.orbit is None:
            return np.zeros(3)
        if obj.name in self.scene_positions:
            return self.scene_positions[obj.name]
        parent = self.system.get_object(obj.parent)
        parent_scene = (self._scene_position(parent, world)
                        if parent is not None else np.zeros(3))
        offset_m = world[obj.name] - world.get(obj.parent, np.zeros(3))
        if obj.parent == "Sun":
            offset = VisualizationTransform.heliocentric_offset(offset_m)
        else:
            offset = offset_m * self.child_scale.get(obj.name, 0.0)
        pos = parent_scene + offset
        self.scene_positions[obj.name] = pos
        return pos

    # =====================================================================
    #  Rendering
    # =====================================================================
    def _safe_color(self, color, fallback=config.BODY_FALLBACK_COLOR):
        try:
            pv.Color(color)
            return color
        except (ValueError, TypeError):
            return fallback

    def _render_body(self, body):
        radius = self.display_radius[body.name]
        mesh = pv.Sphere(radius=radius, center=(0, 0, 0),
                         theta_resolution=config.SPHERE_RESOLUTION,
                         phi_resolution=config.SPHERE_RESOLUTION)
        is_sun = body.parent is None
        actor = self.plotter.add_mesh(
            mesh, color=self._safe_color(body.color), name=body.name,
            smooth_shading=True, lighting=not is_sun,
            specular=0.0 if is_sun else 0.25, specular_power=12,
            ambient=0.9 if is_sun else 0.15)
        actor.position = tuple(self.scene_positions[body.name])
        self._apply_spin(actor, body, self.sim_time_s)
        if is_sun:
            glow = pv.Sphere(radius=radius * 1.25, center=(0, 0, 0))
            g = self.plotter.add_mesh(glow, color=config.SUN_GLOW_COLOR, opacity=0.18,
                                      lighting=False, name=f"{body.name}_glow",
                                      pickable=False)
            g.position = tuple(self.scene_positions[body.name])
        if body.has_ring:
            self._render_ring(body, radius)
        return actor

    def _render_ring(self, body, radius):
        ring = pv.Disc(center=(0, 0, 0), inner=radius * 1.4,
                       outer=radius * 2.3, normal=(0, 0, 1), c_res=64)
        actor = self.plotter.add_mesh(ring, color=config.SATURN_RING_COLOR, opacity=0.6,
                                      lighting=False, name=f"{body.name}_ring",
                                      pickable=False)
        actor.position = tuple(self.scene_positions[body.name])
        actor.orientation = (body.axial_tilt_deg, 0, 0)

    def _render_satellite(self, satellite):
        s = SATELLITE_DISPLAY_SIZE
        dims = np.asarray(satellite.dimensions_m, dtype=float)
        dims = dims / dims.max() * s if dims.max() > 0 else np.array([s, s, s])
        cube = pv.Cube(center=(0, 0, 0), x_length=dims[0],
                       y_length=dims[1], z_length=dims[2])
        actor = self.plotter.add_mesh(
            cube, color=self._safe_color(satellite.color), name=satellite.name,
            smooth_shading=False, specular=0.4, show_edges=True,
            edge_color=config.SATELLITE_EDGE_COLOR)
        actor.position = tuple(self.scene_positions[satellite.name])
        return actor

    def _render_orbits(self):
        for obj in self.system.all_objects():
            if obj.orbit is None or obj.parent is None:
                continue
            local_path_m = self.system.orbit_path_world(obj, {obj.parent: np.zeros(3)})
            if local_path_m is None:
                continue
            if obj.parent == "Sun":
                pts = VisualizationTransform.heliocentric_offset(local_path_m)
            else:
                pts = local_path_m * self.child_scale.get(obj.name, 0.0)
            line = pv.lines_from_points(pts, close=True)
            color = config.ORBIT_COLOR_SATELLITE if isinstance(obj, Satellite) \
                else config.ORBIT_COLOR_BODY
            actor = self.plotter.add_mesh(line, color=color, line_width=1.2,
                                          opacity=0.55, lighting=False,
                                          name=f"{obj.name}_orbit", pickable=False)
            actor.position = tuple(self.scene_positions.get(obj.parent, np.zeros(3)))
            self.orbit_actors[obj.name] = (actor, obj.parent)

    def _build_labels(self):
        self._label_names = [o.name for o in self.system.all_objects()]
        self._update_labels(force=True)

    def _update_labels(self, force: bool = False):
        if not self._labels_visible and not force:
            return
        # Re-add under the same name so the labels actually follow their objects
        # (PyVista snapshots label positions at creation, so mutating in place
        # is not reliable). 11 labels at the animation rate is cheap.
        points = np.array([self.scene_positions[n] for n in self._label_names])
        self.plotter.add_point_labels(
            points, self._label_names, font_size=config.LABEL_FONT_SIZE,
            text_color=config.LABEL_COLOR, point_size=0, shape=None,
            always_visible=True, name="object_labels", pickable=False, render=False)

    def _apply_spin(self, actor, body, time_s):
        period_s = body.rotation_period_h * 3600.0
        spin = (360.0 * time_s / period_s) % 360.0 if period_s != 0 else 0.0
        actor.orientation = (body.axial_tilt_deg, 0.0, spin)

    # =====================================================================
    #  Animation + time controls
    # =====================================================================
    def start_animation(self):
        self._timer.start(int(1000 / ANIMATION_FPS))

    def stop_animation(self):
        self._timer.stop()

    def is_running(self) -> bool:
        return self._timer.isActive()

    def toggle_animation(self) -> bool:
        if self._timer.isActive():
            self._timer.stop()
            return False
        self.start_animation()
        return True

    def set_time_acceleration(self, seconds_per_real_second: float):
        self.time_acceleration = float(seconds_per_real_second)

    def freeze_at_time(self, time_s: float):
        """Jump to a specific simulation time and pause (for inspection)."""
        self._timer.stop()
        self.sim_time_s = time_s
        self._update_positions(self.sim_time_s)
        self._refresh_actor_transforms()
        self.plotter.render()

    def _on_tick(self):
        self.sim_time_s += self.time_acceleration / ANIMATION_FPS
        self._update_positions(self.sim_time_s)
        self._refresh_actor_transforms()
        self.plotter.render()

    def _refresh_actor_transforms(self):
        for name, actor in self.body_actors.items():
            actor.position = tuple(self.scene_positions[name])
            body = self.system.get_object(name)
            if body is not None:
                self._apply_spin(actor, body, self.sim_time_s)
            for suffix in ("_glow", "_ring"):
                extra = self.plotter.actors.get(f"{name}{suffix}")
                if extra is not None:
                    extra.position = tuple(self.scene_positions[name])
        for name, actor in self.satellite_actors.items():
            actor.position = tuple(self.scene_positions[name])
        for name, (actor, parent) in self.orbit_actors.items():
            actor.position = tuple(self.scene_positions.get(parent, np.zeros(3)))
        self._update_labels()

    # =====================================================================
    #  Visibility toggles
    # =====================================================================
    def set_orbits_visible(self, visible: bool):
        self._orbits_visible = visible
        for actor, _ in self.orbit_actors.values():
            actor.SetVisibility(visible)
        self.plotter.render()

    def set_labels_visible(self, visible: bool):
        self._labels_visible = visible
        labels = self.plotter.actors.get("object_labels")
        if labels is not None:
            labels.SetVisibility(visible)
        if visible:
            self._update_labels()
        self.plotter.render()

    # =====================================================================
    #  Inspection (click a body to read its state)
    # =====================================================================
    def _enable_picking(self):
        # use_picker=True makes PyVista pass the VTK picker to the callback, so
        # we can read the EXACT actor under the cursor (not a nearest guess).
        try:
            self.plotter.enable_point_picking(
                callback=self._on_pick, show_message=False,
                use_picker=True, left_clicking=True, picker="cell")
        except (TypeError, AttributeError):
            try:
                self.plotter.enable_point_picking(
                    callback=self._on_pick, show_message=False, use_picker=True)
            except Exception:
                try:
                    self.plotter.enable_point_picking(callback=self._on_pick,
                                                      show_message=False)
                except Exception:
                    pass

    def _actor_to_name(self, actor):
        if actor is None:
            return None
        for name, candidate in self.plotter.actors.items():
            if candidate is actor:
                return name
        return None

    def _on_pick(self, *args):
        """Resolve the clicked object from the picker's actor when available,
        falling back to the nearest body surface otherwise."""
        picker = next((a for a in args if hasattr(a, "GetActor")), None)
        point = next((a for a in args
                      if a is not None and np.ndim(a) == 1 and np.size(a) == 3), None)

        name = None
        if picker is not None:
            try:
                name = self._actor_to_name(picker.GetActor())
            except Exception:
                name = None

        if name not in self.scene_positions and point is not None:
            point = np.asarray(point)

            def score(n):
                return np.linalg.norm(self.scene_positions[n] - point) \
                    - self.display_radius.get(n, 0.6)
            name = min(self.scene_positions, key=score)

        if name in self.scene_positions:
            self._show_inspect(name)

    def _show_inspect(self, name):
        state = self.get_object_state(name)
        if state is None:
            return
        lines = [name]
        if state["parent"]:
            lines.append(f"Distance from {state['parent']}:  {state['radius_km']:,.0f} km")
            lines.append(f"Orbital speed:  {state['speed_kms']:.3f} km/s")
        lines.append(f"Rotation period:  {state['rotation_h']:.2f} h")
        # Replace any previous readout (same actor name) and force a redraw.
        self.plotter.add_text("\n".join(lines), name="inspect",
                              position="upper_left", font_size=config.INSPECT_FONT_SIZE,
                              color=config.INSPECT_TEXT_COLOR)
        self.plotter.render()

    def get_object_state(self, name: str) -> dict | None:
        obj = self.system.get_object(name)
        if obj is None:
            return None
        speed = 0.0
        radius = 0.0
        if obj.orbit is not None and obj.parent is not None:
            mu = self.system.mu_for(obj.parent)
            r, v = orbit.state_vectors_in_parent_frame(obj.orbit, mu, self.sim_time_s)
            speed = np.linalg.norm(v) / 1000.0
            radius = np.linalg.norm(r) / 1000.0
        rotation = getattr(obj, "rotation_period_h", 0.0)
        return {"name": name, "radius_km": radius, "speed_kms": speed,
                "rotation_h": rotation, "parent": obj.parent}

    # =====================================================================
    #  Camera
    # =====================================================================
    def focus_on_body(self, body_name):
        if body_name not in self.scene_positions:
            return
        position = self.scene_positions[body_name]
        radius = self.display_radius.get(body_name, 2.0)
        self.camera_manager.focus_position(position, max(radius * 6, 12))

    def focus_on_satellite(self, satellite_name):
        if satellite_name not in self.scene_positions:
            return
        self.camera_manager.focus_position(self.scene_positions[satellite_name], 8)
