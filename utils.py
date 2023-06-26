import glm
import math

def spherical_to_cartesian(spherical: glm.vec3):
    r = spherical.x
    theta = spherical.y
    phi = spherical.z
    
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    z, x, y = x, y, z
    return glm.vec3(x, y, z)

class Transform:
    def __init__(self, translation: glm.vec3, rotation_yxz: glm.vec3, scale: glm.vec3):
        self.translation = translation
        self.rotation_yxz = rotation_yxz
        self.scale = scale
    
    def get_translate_mat(self):
        return glm.translate(glm.mat4(1), self.translation)
    
    def get_rotation_mat(self):
        rot_y = glm.rotate(self.rotation_yxz.x, glm.vec3(0, 1, 0))
        rot_x = glm.rotate(self.rotation_yxz.y, glm.vec3(1, 0, 0))
        rot_z = glm.rotate(self.rotation_yxz.z, glm.vec3(0, 0, 1))
        return rot_y * rot_x * rot_z
        
    def get_scale_mat(self):
        return glm.scale(glm.mat4(1), self.scale)
    
    def get_transform_mat(self):
        return self.get_translate_mat() * self.get_rotation_mat() * self.get_scale_mat()