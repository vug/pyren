from scene import Scene, Object
from assets import Assets
import utils

import imgui
import glm

import math

class ComboBox:
    def __init__(self, label: str, seq, names, initial_ix=0):
        self.seq = seq
        self.names = names
        self.selected_ix = initial_ix
        self.label = label

    def draw(self):
        _, self.selected_ix = imgui.combo(self.label, self.selected_ix, self.names)
        selected_name = self.names[self.selected_ix]
        selected = self.seq[self.selected_ix]
        return self.selected_ix, selected_name, selected


def transform_widget(obj: Object):
    _, translation = imgui.slider_float3("translation", *obj.transform.translation, min_value=-10.0, max_value=10.0, format="%.3f")
    obj.transform.translation = glm.vec3(translation)
    _, rotation = imgui.slider_float3("rotation (YXZ)", *obj.transform.rotation_yxz, min_value=-10.0, max_value=10.0, format="%.3f")
    obj.transform.rotation_yxz = glm.vec3(rotation)
    _, scale = imgui.slider_float3("scale", *obj.transform.scale, min_value=0.0, max_value=10.0, format="%.3f")
    obj.transform.scale = glm.vec3(scale)


class ImWindows:
    def __init__(self, assets: Assets, scene: Scene):
        self._assets = assets
        self._scene = scene
        self._showAssetsWindow = False
        self._showTextureViewerWindow = True
        self._showInspectorWindow = True
        self._obj_combo = ComboBox("Select Object", list(self._scene.objects.values()), list(self._scene.objects.keys()), 0)
    
    def draw(self):
        if imgui.begin_main_menu_bar().opened:
            if imgui.begin_menu('View', True).opened:
                _, self._showAssetsWindow = imgui.core.menu_item("Assets", None, self._showAssetsWindow)
                _, self._showTextureViewerWindow = imgui.core.menu_item("Texture Viewer", None, self._showTextureViewerWindow)
                _, self._showInspectorWindow = imgui.core.menu_item("Inspector", None, self._showInspectorWindow)
                imgui.end_menu()

            if imgui.begin_menu('Actions', True).opened:
                if imgui.button("reload shaders"):
                    for shader in self._assets.shaders.values():
                        shader.reload()
                imgui.end_menu()

            imgui.end_main_menu_bar()   
       
        if self._showInspectorWindow:
            _, self._showInspectorWindow = draw_inspector_window(self._scene, self._obj_combo)
        if (self._showAssetsWindow):
            _, self._showAssetsWindow = draw_assets_window(self._assets)

cam_r = 3
cam_theta = math.pi / 3
cam_phi = math.pi / 8
def draw_inspector_window(scene, obj_combo):
    global cam_r, cam_theta, cam_phi
    has_clicked, is_open = imgui.begin("Inspector", True)            
    if (len(scene.objects) > 0):
        _, obj_name, obj = obj_combo.draw()
        imgui.text(f"selected: {obj_name}")
        transform_widget(obj)    
        imgui.separator()   
       
    # TODO: move orbit camera UI to utils
    _, cam_r = imgui.slider_float("cam pos r", cam_r, 0.01, 10, "%.3f")
    _, cam_theta = imgui.slider_float("cam pos theta", cam_theta, 0.0, math.pi, "%.3f")
    _, cam_phi = imgui.slider_float("cam pos phi", cam_phi, 0.01, 2.0 * math.pi, "%.3f")
    scene.cam.position = utils.spherical_to_cartesian(glm.vec3(cam_r, cam_theta, cam_phi))
    imgui.separator()

    _, (scene.clear_color.r, scene.clear_color.g, scene.clear_color.b) = imgui.color_edit3("Clear Color", *scene.clear_color)
    _, (scene.ambient_light.color.r, scene.ambient_light.color.g, scene.ambient_light.color.b) = imgui.color_edit3("Ambient.Color", *scene.ambient_light.color)
    _, (scene.directional_light.direction.x, scene.directional_light.direction.y, scene.directional_light.direction.z) = imgui.drag_float3("Directional.Direction", *scene.directional_light.direction, change_speed=0.1)
    _, scene.directional_light.intensity = imgui.drag_float("Directional.Intensity", scene.directional_light.intensity, change_speed=0.1, min_value=0.0)
    _, (scene.directional_light.color.r, scene.directional_light.color.g, scene.directional_light.color.b) = imgui.color_edit3("Directional.Color", *scene.directional_light.color)
    _, scene.hemispherical_light.intensity = imgui.drag_float("Hemispherical.Intensity", scene.hemispherical_light.intensity, change_speed=0.1, min_value=0.0)
    _, (scene.hemispherical_light.north_color.r, scene.hemispherical_light.north_color.g, scene.hemispherical_light.north_color.b) = imgui.color_edit3("Hemispherical.NorthColor", *scene.hemispherical_light.north_color)
    _, (scene.hemispherical_light.south_color.r, scene.hemispherical_light.south_color.g, scene.hemispherical_light.south_color.b) = imgui.color_edit3("Hemispherical.SouthColor", *scene.hemispherical_light.south_color)
    for point_light in scene.point_lights:
        _, (point_light.position.x, point_light.position.y, point_light.position.z) = imgui.drag_float3(f"PointLight[{point_light.ix}].Position", *point_light.position, change_speed=0.1)
        _, point_light.intensity = imgui.drag_float("PointLight[{pointLight.ix}].Intensity", point_light.intensity, change_speed=0.1, min_value=0.0)
        _, (point_light.color.r, point_light.color.g, point_light.color.b) = imgui.color_edit3(f"PointLight[{point_light.ix}].Color", *point_light.color)
    imgui.end()
    return has_clicked, is_open

def draw_assets_window(assets):
    has_clicked, is_open = imgui.begin("Assets", True)
    imgui.text("Meshes (name, vao, #vertices):")
    for name, mesh in assets.meshes.items():
        imgui.text(f"{name}, {mesh.vao}, {mesh.vertex_count}")
    imgui.separator()
    imgui.text("Shaders (name, program, vertex, fragment)")
    for name, shader in assets.shaders.items():
        imgui.text(f"{name}, {shader.get_id()}, {shader.vertex_file}, {shader.fragment_file}")
    imgui.end()
    return has_clicked, is_open

def draw_texture_viewer_window(tex_combo):
        has_clicked, is_open = imgui.begin("Texture Viewer", True, imgui.WINDOW_NO_SCROLLBAR)
        _, _, viz_tex = tex_combo.draw()
        imgui.separator()             
        available_sz = imgui.get_content_region_available()
        imgui.core.get_content_region_available_width()
        win_ar = available_sz.x / available_sz.y
        tex_ar = viz_tex.desc.width / viz_tex.desc.height
        w, h = 1, 1
        if tex_ar >= win_ar:
            w = available_sz.x
            h = w / tex_ar
        else:
            h = available_sz.y
            w = h * tex_ar
        imgui.image(viz_tex.get_id(), w, h, uv0=(0, 1), uv1=(1, 0), border_color=(1,1,0,1))
        imgui.end()
        return has_clicked, is_open