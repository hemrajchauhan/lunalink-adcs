import pyvista as pv
import numpy as np

from ...simulation.repositories.body_repository import BodyRepository
from ...simulation.repositories.satellite_repository import SatelliteRepository
from .transforms import VisualizationTransform
from .camera_manager import CameraManager

class SceneManager:

    def __init__(self, plotter):
        self.plotter = plotter

        self.camera_manager = CameraManager(self.plotter)
        
        self.celestial_bodies = []
        self.satellites = []

        self.body_actors = {}
        self.satellite_actors = {}

    def _configure_renderer(self):
        self.plotter.set_background("black")
        self.plotter.show_axes()
        self.plotter.enable_lightkit()

    def _render_body(self, body):
        render_position = VisualizationTransform.position(body.position_m)
        render_radius = VisualizationTransform.radius(body.radius_m)

        mesh = pv.Sphere(radius=render_radius, center=render_position)
        actor = self.plotter.add_mesh(mesh, color=body.color, name=body.name, smooth_shading=True, show_edges=True)

        self.plotter.add_point_labels([render_position], [body.name], 
                                      font_size=12, text_color="white",
                                      point_size=0, name=f"{body.name}_label")

        return actor

    def _render_satellite(self, satellite):
        render_position = VisualizationTransform.position(satellite.position_m)

        x_length, y_length, z_length = VisualizationTransform.satellite_dimensions(satellite.dimensions_m)
        
        cube = pv.Cube(center=render_position, x_length=x_length, 
                       y_length=y_length, z_length=z_length)
        actor = self.plotter.add_mesh(cube, color=satellite.color, name=satellite.name, smooth_shading=True, show_edges=True)
        
        self.plotter.add_point_labels([render_position], [satellite.name], 
                                      font_size=12, text_color="white",
                                      point_size=0, name=f"{satellite.name}_label")
        return actor
    
    def _set_default_camera(self):
        self.plotter.camera_position = 'iso'
        self.plotter.reset_camera()

    def setup_scene(self):
        self._configure_renderer()
        
        body_repository = BodyRepository()
        self.celestial_bodies = body_repository.load_all()

        satellite_repository = SatelliteRepository()
        self.satellites = satellite_repository.load_all()

        for body in self.celestial_bodies:
            body_actor = self._render_body(body)
            self.body_actors[body.name] = body_actor

        for satellite in self.satellites:
            satellite_actor = self._render_satellite(satellite)
            self.satellite_actors[satellite.name] = satellite_actor

        self.focus_on_body("Earth")

    def reload_scene(self):
        self.plotter.clear()
        self.body_actors.clear()
        self.satellite_actors.clear()
        self.celestial_bodies.clear()
        self.satellites.clear()
        self.setup_scene()

    def focus_on_body(self, body_name):
        body = next((b for b in self.celestial_bodies if b.name == body_name), None)
        if body is None:
            return
        render_position = VisualizationTransform.position(body.position_m)
        focus_distance = max(VisualizationTransform.radius(body.radius_m) * 10, 100)
        self.camera_manager.focus_position(render_position, focus_distance)

    def focus_on_satellite(self, satellite_name):
        satellite = next((s for s in self.satellites if s.name == satellite_name), None)
        if satellite is None:
            return
        render_position = VisualizationTransform.position(satellite.position_m)
        self.camera_manager.focus_position(render_position, 200)