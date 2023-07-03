from shader import Shader

import glm

class AmbientLight:
    def __init__(self, color=glm.vec3(0, 0, 0)):
        self.color: glm.vec3 = color

    def upload_to_shader(self, shader: Shader):
        shader.set_uniform_vec3('ambientLight.color', self.color)

class DirectionalLight:
    def __init__(self, direction=glm.vec3(0, -1, 0), intensity=1.0, color=glm.vec3(1, 1, 1)):
        self.direction=direction
        self.intensity = intensity
        self.color = color
    
    def upload_to_shader(self, shader: Shader):
        shader.set_uniform_vec3('directionalLight.direction', self.direction)
        shader.set_uniform_float1('directionalLight.intensity', self.intensity)
        shader.set_uniform_vec3('directionalLight.color', self.color)