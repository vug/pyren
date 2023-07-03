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

class HemisphericalLight:
    def __init__(self, intensity=0.0, north_color=glm.vec3(53, 191, 179)/255, south_color=glm.vec3(144, 12, 63)/255):
        self.intensity = intensity
        self.north_color = north_color
        self.south_color = south_color
        
    def upload_to_shader(self, shader: Shader):
        shader.set_uniform_float1('hemisphericalLight.intensity', self.intensity)
        shader.set_uniform_vec3('hemisphericalLight.northColor', self.north_color)
        shader.set_uniform_vec3('hemisphericalLight.southColor', self.south_color)