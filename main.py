"""
Ref:
- GitHub - jcteng/python-opengl-tutorial: Python opengl-tutorial base on PyOpenGL. https://github.com/jcteng/python-opengl-tutorial
- python - How do I make OpenGL draw do a non-display surface in pygame? - Stack Overflow https://stackoverflow.com/questions/53748691/how-do-i-make-opengl-draw-do-a-non-display-surface-in-pygame

TODO:
* Add multiple point lights https://learnopengl.com/Advanced-Lighting/Deferred-Shading, https://ogldev.org/www/tutorial36/tutorial36.html
* BLIT selected texture into default framebuffer, instead of visualizing it in a separate ImGui window

TODO LATER:
* calculate normals if not provided (Ex: bunny.obj)
* move logic in create_mesh_buffer into Mesh
* (Maybe later) load image file into texture
* add post-processing effects https://learnopengl.com/Advanced-OpenGL/Framebuffers
* Texture viewer/editor: https://docs.gl/gl4/glTexParameter, debug https://registry.khronos.org/OpenGL-Refpages/gl4/html/glGetFramebufferAttachmentParameter.xhtml

REF:
* pyopengl example: https://gist.github.com/vug/2c7953d5fdf750c727af249ded3e9018
* https://github.com/vug/graphics-app-boilerplate
* https://github.com/vug/render-graph-study
"""
from assets import Assets
import renderer as rndr
from scene import Scene, Object
import utils

import glm
import imgui
import numpy as np
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_COMPONENT32,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_BUFFER_BIT,
    GL_FLOAT,
    GL_INT,
    GL_RED_INTEGER,
    GL_RG,
    GL_RGB,
    GL_RGB8,
    GL_RG32F,
    GL_R32I,
    GL_RGB32F,
    GL_TRIANGLES,
    GL_UNSIGNED_BYTE,
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
    renderer.init()
    
    scene = Scene(renderer)
    scene.clear_color = glm.vec3([0.0, 0.0, 0.4])
    
    scene_tex = renderer.make_tex_3channel_8bit()
    world_pos_tex = renderer.make_tex_3channel_flt32()
    world_normal_tex = renderer.make_tex_3channel_flt32()
    uv_tex = renderer.make_tex_2channel_flt32()
    mesh_id_tex = renderer.make_tex_1channel_int32()
    mesh_id_colored_tex = renderer.make_tex_3channel_8bit()
    # TODO: add a color texture for depth (by calculating distance from camera)
        
    fb = rndr.Framebuffer(
        color_textures=[scene_tex, world_pos_tex, world_normal_tex, uv_tex, mesh_id_tex, mesh_id_colored_tex], 
        depth_texture=renderer.make_default_depth_tex()
    )
    
    # TODO: resizable Framebuffers
    # TODO: register Framebuffers to renderer for auto-resize
    
    #globals().update(locals())
    
    assets = Assets(renderer)
    assets.load_obj("monkey", "models/monkey.obj")
    assets.load_obj("ship", "models/ship.obj")
    assets.load_obj("cubeTri", "models/cubeTri.obj")
    assets.load_obj("quad", "models/quad.obj")
    assets.load_obj("sphere", "models/sphere.obj")
    # assets.load_obj("bunny", "models/bunny.obj")
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
    # TODO: UI that lists loaded assets. For mesh show name, vertex and triangle count
    # TODO: bring a quad mesh asset
    # TODO: add 1 ground object with a quad
    # TODO: add 1 rectangular area light
    # TODO: UI for area light
    # TODO: visualize area light with a quad
    # TODO: render area light with 4 point lights at corners
    
    # TODO: move camera stuff to utils > orbit camera
    cam_r = 3
    cam_theta = math.pi / 3
    cam_phi = math.pi / 8
    selected_ix = 0
    selected_tex_ix = 0
    
    while renderer.is_running():
        renderer.begin_frame()
        # glViewport(0, 0, renderer.win_size.x, renderer.win_size.y);
        
        imgui.begin("Settings", True)
        
        if imgui.button("reload shader"):
            for shader in assets.shaders.values():
                shader.reload()
        imgui.separator()
        
        if (len(objects) > 0):
            obj_names = list(objects.keys())
            _, selected_ix = imgui.combo("Select Object", selected_ix, obj_names)
            obj = objects[obj_names[selected_ix]]
            imgui.text(f"selected: {obj_names[selected_ix]}")
            # TODO: move transfrom UI to utils
            _, translation = imgui.slider_float3("translation", *obj.transform.translation, min_value=-10.0, max_value=10.0, format="%.3f")
            obj.transform.translation = glm.vec3(translation)
            _, rotation = imgui.slider_float3("rotation (YXZ)", *obj.transform.rotation_yxz, min_value=-10.0, max_value=10.0, format="%.3f")
            obj.transform.rotation_yxz = glm.vec3(rotation)
            _, scale = imgui.slider_float3("scale", *obj.transform.scale, min_value=0.0, max_value=10.0, format="%.3f")
            obj.transform.scale = glm.vec3(scale)        
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
        
        for obj_name, obj in objects.items():
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
        
        imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(0, 0))
        imgui.begin("Scene", True)
        viz_tex_names = ["scene", "world_pos", "world_normal", "uv", "mesh_id", "mesh_id_colored"]
        _, selected_tex_ix = imgui.combo("Select Texture", selected_tex_ix, viz_tex_names)
        viz_tex = fb.color_textures[selected_tex_ix]
        imgui.image(viz_tex.get_id(), viz_tex.desc.width, viz_tex.desc.height, uv0=(1, 1), uv1=(0, 0), border_color=(1,1,0,1))
        imgui.end()
        imgui.pop_style_var(1)
        
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