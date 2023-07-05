import glm
import imgui
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


"""
My implementation of ImGui::DockSpaceOverViewport from
https://github.com/ocornut/imgui/blob/dc3e531ff28450bff73fde0163b1d076b6bb5605/imgui.cpp#L17866 
Because it's not implemented in pyimgui's docking branch yet (https://github.com/pyimgui/pyimgui/issues/259#issuecomment-1039239640)
"""
def imgui_dockspace_over_viewport():
    viewport = imgui.get_main_viewport()
    imgui.set_next_window_position(viewport.work_pos.x, viewport.work_pos.y)
    imgui.set_next_window_size(viewport.work_size.x, viewport.work_size.y)
    imgui.set_next_window_viewport(viewport.id)
    host_window_flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_DOCKING;
    host_window_flags |= imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS | imgui.WINDOW_NO_NAV_FOCUS
    dockspace_flags = 0
    if (dockspace_flags & imgui.DOCKNODE_PASSTHRU_CENTRAL_NODE):
        host_window_flags |= imgui.WINDOW_NO_BACKGROUND;        
    label = f"DockSpaceViewport_{viewport.id}"
    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0)
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(0.0, 0.0))
    imgui.begin(label, None, host_window_flags)
    imgui.pop_style_var(3)
    dockspace_id = imgui.get_id("DockSpace")
    imgui.dockspace(dockspace_id, (0.0, 0.0), dockspace_flags)
    # imgui.dockspace(dockspace_id, imgui.Vec2(0.0, 0.0), dockspace_flags, window_class)
    imgui.end() 