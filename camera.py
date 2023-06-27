import glm

class Camera:
    up = glm.vec3(0, 1, 0)

    def __init__(self, position, target, fov, aspect_ratio):
        self.position = position
        self.target = target
        self.fov = fov
        self.aspect_ratio = aspect_ratio
        self.near_clip = 0.01
        self.far_clip = 100.0

    # def get_direction(self):
    #     # cos/sin x/y/z order taken from: https://learnopengl.com/code_viewer_gh.php?code=includes/learnopengl/camera.h
    #     pitch, yaw, roll = self.orientation
    #     return glm.vec3(
    #         math.cos(yaw) * math.cos(pitch),
    #         math.sin(pitch),
    #         math.sin(yaw) * math.cos(pitch)
    #     )

    def get_view_from_world(self):
        return glm.lookAt(self.position, self.target, self.up)

    def get_projection_from_view(self):
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near_clip, self.far_clip)