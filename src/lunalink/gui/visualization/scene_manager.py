import pyvista as pv

class SceneManager:

    def __init__(self, plotter):
        self.plotter = plotter

    def setup_scene(self):
        self.plotter.set_background("black")
        self.plotter.add_axes()