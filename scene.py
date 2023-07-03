from camera import Camera
from lights import AmbientLight, DirectionalLight

import glm

class Scene:
    def __init__(self, renderer):
        self.renderer = renderer
        self.clear_color = glm.vec3(1, 1, 1)
        self.objects: dict[str, Object] = {}
        self.cam = Camera(position=glm.vec3(0.5, 0.5, -3), target=glm.vec3(0, 0, 0), fov=50, aspect_ratio=renderer.win_size[0] / renderer.win_size[1])
        self.ambient_light: AmbientLight = AmbientLight()
        self.directional_light: DirectionalLight = DirectionalLight()

class Object:
    def __init__(self, mesh, transform, shader):
        self.mesh = mesh
        self.transform = transform
        self.shader = shader