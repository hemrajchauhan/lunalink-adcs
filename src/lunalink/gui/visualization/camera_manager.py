import numpy as np

class CameraManager:

    def __init__(self, plotter):
        self.plotter = plotter

    def reset(self):
        self.plotter.camera_position = 'iso'
        self.plotter.reset_camera()

    def focus_position(self, position, distance):

        position = np.asarray(position)

        camera_position = position + np.array([distance, distance, distance])

        self.plotter.camera.position = camera_position
        self.plotter.camera.focal_point = position
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()
