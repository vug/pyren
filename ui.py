from datetime import datetime
import math
import png

import glm
import imgui
import numpy as np
from OpenGL.GL import glGetTextureImage

from assets import Assets
from scene import Scene, Object
from texture import Texture
import utils


class ComboBox:
    def __init__(self, label: str, seq, names, initial_ix=0):
        self.seq = seq
        self.names = names
        self.selected_ix = initial_ix
        self.label = label

    def draw(self) -> tuple[int, str, Texture]:
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
    def __init__(self, assets: Assets, scene: Scene, viewport_size: glm.ivec2):
        self._assets = assets
        self._scene = scene
        self._show_assets_window = True
        self._show_texture_viewer_window = True
        self._show_inspector_window = True
        self._show_imgui_demo_window = False
        self._show_viewport_window = True
        self._obj_combo = ComboBox("Select Object", list(self._scene.objects.values()), list(self._scene.objects.keys()), 0)
        self._tex_combo = ComboBox("Select Texture", list(self._assets.textures.values()), list(self._assets.textures.keys()))
        self.viewport_size = viewport_size

        # Camera state (maybe should be somewhere else, scene?)
        self.cam_r = 3
        self.cam_theta = math.pi / 3
        self.cam_phi = math.pi / 8
    
    def draw(self):
        if imgui.begin_main_menu_bar().opened:
            if imgui.begin_menu('View', True).opened:
                _, self._show_assets_window = imgui.core.menu_item("Assets", None, self._show_assets_window)
                _, self._show_texture_viewer_window = imgui.core.menu_item("Texture Viewer", None, self._show_texture_viewer_window)
                _, self._show_inspector_window = imgui.core.menu_item("Inspector", None, self._show_inspector_window)
                _, self._show_imgui_demo_window = imgui.core.menu_item("ImGui Demo Window", None, self._show_imgui_demo_window)
                # _, self._show_viewport_window = imgui.core.menu_item("Viewport Window", None, self._show_viewport_window)
                imgui.end_menu()

            if imgui.begin_menu('Actions', True).opened:
                if imgui.button("reload shaders"):
                    for name, shader in self._assets.shaders.items():
                        result = shader.reload()
                        if result != -1:
                            print(f"Shader '{name}' reloaded successfully.")
                imgui.end_menu()

            imgui.end_main_menu_bar()   
       
        if self._show_inspector_window:
            _, self._show_inspector_window = self.draw_inspector_window(self._scene, self._obj_combo)
        if (self._show_assets_window):
            _, self._show_assets_window = ImWindows.draw_assets_window(self._assets)
        if (self._show_texture_viewer_window):
            _, self._show_texture_viewer_window = ImWindows.draw_texture_viewer_window(self._tex_combo)
        if (self._show_imgui_demo_window):
            imgui.show_demo_window()
        if (self._show_viewport_window):
            _, self._show_viewport_window = self.draw_viewport_window(self._assets.textures["viewport"])


    def draw_viewport_window(self, viewport_tex):
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(0.0, 0.0))
        has_clicked, is_open = imgui.begin("Viewport", False, imgui.WINDOW_NO_SCROLLBAR)
        w, h = imgui.get_content_region_available()
        self.viewport_size = glm.ivec2(w, h)
        imgui.image(viewport_tex.get_id(), w, h, uv0=(0, 1), uv1=(1, 0), border_color=(1,1,0,1))
        imgui.end()
        imgui.pop_style_var(1)
        return has_clicked, is_open


    def draw_inspector_window(self, scene, obj_combo):
        has_clicked, is_open = imgui.begin("Inspector", True)
        if (len(scene.objects) > 0):
            _, obj_name, obj = obj_combo.draw()
            imgui.text(f"selected: {obj_name}")
            transform_widget(obj)
            imgui.separator()
        
        # TODO: move orbit camera UI to utils
        _, self.cam_r = imgui.slider_float("cam pos r", self.cam_r, 0.01, 10, "%.3f")
        _, self.cam_theta = imgui.slider_float("cam pos theta", self.cam_theta, 0.0, math.pi, "%.3f")
        _, self.cam_phi = imgui.slider_float("cam pos phi", self.cam_phi, 0.01, 2.0 * math.pi, "%.3f")
        scene.cam.position = utils.spherical_to_cartesian(glm.vec3(self.cam_r, self.cam_theta, self.cam_phi))
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
            _, point_light.intensity = imgui.drag_float(f"PointLight[{point_light.ix}].Intensity", point_light.intensity, change_speed=0.1, min_value=0.0)
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

    def draw_texture_viewer_window(tex_combo: ComboBox):
            has_clicked, is_open = imgui.begin("Texture Viewer", True, imgui.WINDOW_NO_SCROLLBAR)
            _, tex_name, tex = tex_combo.draw()
            imgui.same_line()
            if imgui.button("save"):
                filename = f"{tex_name}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.png"
                print(f"saving {filename}...")
                desc = tex.desc
                num_channels = desc.num_channels()
                pixels = np.empty(shape=(desc.width, desc.height, num_channels), dtype=desc.dtype())
                # pixels[:, :, 3] = 255 if pixels.dtype == np.uint8 else 1
                glGetTextureImage(tex.get_id(), 0, desc.format, desc.type, pixels.size * pixels.itemsize, pixels)
                pixels = np.flip(pixels, axis=(0, 1))  # OpenGL images are inverted on y-axis
                # TODO: for now we only have PNG format. Can bring TIFF to save image files with floating point channels
                if pixels.dtype != np.uint8:
                    pixels = (pixels * 255.99).clip(min=0.0, max=255.99).astype(np.uint8)
                # Make 2- and 1-channel images 3-channel RGB (png module saves 2-channel images as grayscale w/alpha)
                if num_channels == 2:
                    pixels = np.concatenate((pixels, np.zeros(shape=(pixels.shape[0], pixels.shape[1], 1), dtype=pixels.dtype)), axis=2)
                    num_channels = 3
                if num_channels == 1:
                    pixels = np.concatenate((pixels, np.zeros(shape=(pixels.shape[0], pixels.shape[1], 2), dtype=pixels.dtype)), axis=2)
                    num_channels = 3
                pixels = pixels.reshape(-1, desc.width * num_channels)
                png_mode = {4: "RGBA", 3: "RGB", 2: "RGB", 1: "RGB"}[desc.num_channels()]  # correct: {4: "RGBA", 3: "RGB", 2: "LA", 1: "L"}
                png.from_array(pixels, mode=png_mode).save(filename)
            imgui.separator()
            available_sz = imgui.get_content_region_available()
            win_ar = available_sz.x / available_sz.y
            tex_ar = tex.desc.width / tex.desc.height
            w, h = 1, 1
            if tex_ar >= win_ar:
                w = available_sz.x
                h = w / tex_ar
            else:
                h = available_sz.y
                w = h * tex_ar
            imgui.image(tex.get_id(), w, h, uv0=(0, 1), uv1=(1, 0))  # border_color=(1,1,0,1)
            imgui.end()
            return has_clicked, is_open