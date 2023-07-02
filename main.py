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
    assets.load_shader("default", "shaders/default.vert", "shaders/default.frag")
    assets.load_shader("fullscreen", "shaders/fullscreen_quad.vert", "shaders/fullscreen_quad.frag")
    
    scene.objects["suzanne"] = Object(
        mesh=assets.meshes["monkey"], 
        transform=utils.Transform(translation=glm.vec3(0.5, 0.5, 0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.3, .3, .3)),
        shader=assets.shaders["default"]
    )
    scene.objects["space_ship"] = Object(
        mesh=assets.meshes["ship"], 
        transform=utils.Transform(translation=glm.vec3(-0.5, -0.5, -0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.1, .1, .1)),
        shader=assets.shaders["default"]
    )
    scene.objects["sphere"] = Object(
        mesh=assets.meshes["sphere"], 
        transform=utils.Transform(translation=glm.vec3(0.5, 0.5, -0.5), rotation_yxz=glm.vec3(0, 0, 0), scale=glm.vec3(.1, .1, .1)),
        shader=assets.shaders["default"]
    )
    
    obj_combo = ui.ComboBox("Select Object", list(scene.objects.values()), list(scene.objects.keys()), 0)
    tex_names = ["scene", "world_pos", "world_normal", "uv", "depth", "mesh_id", "mesh_id_colored"]
    assert(len(tex_names) == len(fb.color_textures))
    tex_combo = ui.ComboBox("Select Texture", fb.color_textures, tex_names)
    showAssetsWindow = False
    showTextureViewerWindow = True
    showInspectorWindow = True
    
    while renderer.is_running():
        renderer.begin_frame()
        fb.resize_if_needed(renderer.win_size.x, renderer.win_size.y)
        scene.cam.aspect_ratio = renderer.win_size.x / renderer.win_size.y
        glViewport(0, 0, renderer.win_size.x, renderer.win_size.y)

        
        if imgui.begin_main_menu_bar().opened:
            if imgui.begin_menu('View', True).opened:
                _, showAssetsWindow = imgui.core.menu_item("Assets", None, showAssetsWindow)
                _, showTextureViewerWindow = imgui.core.menu_item("Texture Viewer", None, showTextureViewerWindow)
                _, showInspectorWindow = imgui.core.menu_item("Inspector", None, showInspectorWindow)
                imgui.end_menu()

            if imgui.begin_menu('Actions', True).opened:
                if imgui.button("reload shaders"):
                    for shader in assets.shaders.values():
                        shader.reload()
                imgui.end_menu()

            imgui.end_main_menu_bar()   
       
        if showInspectorWindow:
            _, showInspectorWindow = ui.draw_inspector_window(scene, obj_combo)
                      
        fb.bind()
        # TODO: scene has a clear method `clear(color=True, depth=True)`
        glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        for _, obj in scene.objects.items():
            # TODO maybe: a scene.render_object() method (might take uniforms)
            obj.shader.bind()
            glBindVertexArray(obj.mesh.vao)
            obj.shader.set_uniform_mat4("worldFromObject", obj.transform.get_transform_mat())
            obj.shader.set_uniform_mat4("viewFromWorld", scene.cam.get_view_from_world())
            obj.shader.set_uniform_mat4("projectionFromView", scene.cam.get_projection_from_view())
            obj.shader.set_uniform_vec3("eyePos", scene.cam.position)
            obj.shader.set_uniform_int1("meshId", obj.mesh.vao)
            scene.ambient_light.upload_to_shader(obj.shader)
            glDrawArrays(GL_TRIANGLES, 0, obj.mesh.vertex_count)
            glBindVertexArray(0)
            obj.shader.unbind()
        fb.unbind()

        glActiveTexture(GL_TEXTURE0)
        scene_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 1)
        world_pos_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 2)
        world_normal_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 3)
        uv_tex.bind()
        glActiveTexture(GL_TEXTURE0 + 4)
        mesh_id_tex.bind()
        
        # Clear editor background
        glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        assets.shaders["fullscreen"].bind()
        assets.shaders["fullscreen"].set_uniform_vec3("eyePos", scene.cam.position)
        scene.ambient_light.upload_to_shader(obj.shader)
        glBindVertexArray(renderer.empty_vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        assets.shaders["fullscreen"].unbind()

        if (showAssetsWindow):
            _, showAssetsWindow = ui.draw_assets_window(assets)
        if (showTextureViewerWindow):
            _, showTextureViewerWindow = ui.draw_texture_viewer_window(tex_combo)        
    
        renderer.end_frame()
        
    renderer.deinit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        renderer.deinit()