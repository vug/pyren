from shader import Shader

import glm

class AmbientLight:
    def __init__(self, color=glm.vec3(0, 0, 0)):
        self.color: glm.vec3 = color

    def upload_to_shader(self, shader: Shader):
        shader.set_uniform_vec3('ambientLight.color', self.color)