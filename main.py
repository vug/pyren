"""
TODO:
* Add multiple point lights https://learnopengl.com/Advanced-Lighting/Deferred-Shading, https://ogldev.org/www/tutorial36/tutorial36.html
* BLIT selected texture into default framebuffer, instead of visualizing it in a separate ImGui window

REF:
* pyopengl example: https://gist.github.com/vug/2c7953d5fdf750c727af249ded3e9018
* https://github.com/vug/graphics-app-boilerplate
* https://github.com/vug/render-graph-study
"""
from assets import Assets
from framebuffer import Framebuffer
import renderer as rndr
from scene import Scene, Object
import ui
import utils

import glm
import imgui
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_TRIANGLES,
    glBindVertexArray,
    glClear,
    glClearColor,
    glDrawArrays,
    #
    glActiveTexture, GL_TEXTURE0, glViewport

)  # everything here starts with glXYZ or GL_XYZ

import math
import traceback

renderer = rndr.Renderer()

def main():   
    renderer.init(1024, 768)
    
    scene = Scene(renderer)
    scene.clear_color = glm.vec3([0.0, 0.0, 0.4])
    
    scene_tex = renderer.make_tex_3channel_8bit()
    world_pos_tex = renderer.make_tex_3channel_flt32()
    world_normal_tex = renderer.make_tex_3channel_flt32()
    uv_tex = renderer.make_tex_2channel_flt32()
    mesh_id_tex = renderer.make_tex_1channel_int32()
    mesh_id_colored_tex = renderer.make_tex_3channel_8bit()
    my_depth_tex = renderer.make_tex_1channel_flt32()  # actually a color attachment
    fb = Framebuffer(
        color_textures=[scene_tex, world_pos_tex, world_normal_tex, uv_tex, my_depth_tex, mesh_id_tex, mesh_id_colored_tex], 
        depth_texture=renderer.make_default_depth_tex()
    )
    
    #globals().update(locals())
    
    assets = Assets(renderer)
    assets.load_obj("monkey", "models/monkey.obj")
    assets.load_obj("ship", "models/ship.obj")
    assets.load_obj("cubeTri", "models/cubeTri.obj")
    assets.load_obj("quad", "models/quad.obj")
    assets.load_obj("sphere", "models/sphere.obj")
    assets.load_shader("default", "default.vert", "default.frag")
    assets.load_shader("fullscreen", "fullscreen_quad.vert", "fullscreen_quad.frag")
    
    objects = {}
    objects["suzanne"] = Object(
        mesh=assets.meshes["monkey"], 
        transform=utils.Transform(translation=glm.vec3(0.5, 0.5, 0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.3, .3, .3)),
        shader=assets.shaders["default"]
    )
    objects["space_ship"] = Object(
        mesh=assets.meshes["ship"], 
        transform=utils.Transform(translation=glm.vec3(-0.5, -0.5, -0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.1, .1, .1)),
        shader=assets.shaders["default"]
    )
    objects["sphere"] = Object(
        mesh=assets.meshes["sphere"], 
        transform=utils.Transform(translation=glm.vec3(0.5, 0.5, -0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.1, .1, .1)),
        shader=assets.shaders["default"]
    )
    
    # TODO: move camera stuff to utils > orbit camera
    cam_r = 3
    cam_theta = math.pi / 3
    cam_phi = math.pi / 8

    obj_combo = ui.ComboBox("Select Object", list(objects.values()), list(objects.keys()), 0)
    tex_names = ["scene", "world_pos", "world_normal", "uv", "depth", "mesh_id", "mesh_id_colored"]
    assert(len(tex_names) == len(fb.color_textures))
    tex_combo = ui.ComboBox("Select Texture", fb.color_textures, tex_names)
    
    while renderer.is_running():
        renderer.begin_frame()
        fb.resize_if_needed(renderer.win_size.x, renderer.win_size.y)
        scene.cam.aspect_ratio = renderer.win_size.x / renderer.win_size.y
        glViewport(0, 0, renderer.win_size.x, renderer.win_size.y)

        ui.draw_assets_window(assets)
        
        imgui.begin("Settings", True)
        
        if imgui.button("reload shaders"):
            for shader in assets.shaders.values():
                shader.reload()
        imgui.separator()
                
        if (len(objects) > 0):
            _, obj_name, obj = obj_combo.draw()
            imgui.text(f"selected: {obj_name}")
            ui.transform_widget(obj)    
            imgui.separator()
        
        # TODO: use color-picker for clear color UI
        # TODO: move clear color UI to utils
        _, clear_color = imgui.slider_float3("Clear Color", *scene.clear_color, min_value=0.0, max_value=1.0, format="%.3f")
        scene.clear_color = glm.vec3(clear_color)
        imgui.separator()
        
        # TODO: move orbit camera UI to utils
        _, cam_r = imgui.slider_float("cam pos r", cam_r, 0.01, 10, "%.3f")
        _, cam_theta = imgui.slider_float("cam pos theta", cam_theta, 0.0, math.pi, "%.3f")
        _, cam_phi = imgui.slider_float("cam pos phi", cam_phi, 0.01, 2.0 * math.pi, "%.3f")
        scene.cam.position = utils.spherical_to_cartesian(glm.vec3(cam_r, cam_theta, cam_phi))
        
        imgui.end()
                      
        fb.bind()
        # TODO: scene has a clear method `clear(color=True, depth=True)`
        glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        for _, obj in objects.items():
            # TODO maybe: a scene.render_object() method (might take uniforms)
            obj.shader.bind()
            glBindVertexArray(obj.mesh.vao)
            obj.shader.set_uniform_mat4("worldFromObject", obj.transform.get_transform_mat())
            obj.shader.set_uniform_mat4("viewFromWorld", scene.cam.get_view_from_world())
            obj.shader.set_uniform_mat4("projectionFromView", scene.cam.get_projection_from_view())
            obj.shader.set_uniform_vec3("eyePos", scene.cam.position)
            obj.shader.set_uniform_int1("meshId", obj.mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, obj.mesh.vertex_count)
            glBindVertexArray(0)
            obj.shader.unbind()
        fb.unbind()
        
        imgui.begin("Texture Viewer", True, imgui.WINDOW_NO_SCROLLBAR)
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
        
        glActiveTexture(GL_TEXTURE0)
        scene_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 1)
        world_pos_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 2)
        world_normal_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 3)
        uv_tex.bind()
        
        # Clear editor background
        glClearColor(0.2, 0.3, 0.4, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        assets.shaders["fullscreen"].bind()
        assets.shaders["fullscreen"].set_uniform_vec3("eyePos", scene.cam.position)
        glDrawArrays(GL_TRIANGLES, 0, 3)
    
        renderer.end_frame()
        
    renderer.deinit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        renderer.deinit()