"""
TODO:
* Add multiple point lights https://learnopengl.com/Advanced-Lighting/Deferred-Shading, https://ogldev.org/www/tutorial36/tutorial36.html

REF:
* pyopengl example: https://gist.github.com/vug/2c7953d5fdf750c727af249ded3e9018
* https://github.com/vug/graphics-app-boilerplate
* https://github.com/vug/render-graph-study
"""
from assets import Assets
from framebuffer import Framebuffer
from lights import PointLight
from renderer import Renderer
from scene import Scene, Object
from texture import Texture, PixelBuffer
import ui
import utils

import glm
import glfw
import numpy as np
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear, glClearColor,
    GL_TRIANGLES, glBindVertexArray, glDrawArrays,
    glActiveTexture, GL_TEXTURE0,
    glReadBuffer, GL_COLOR_ATTACHMENT0, glReadPixels, GL_RGB, GL_FLOAT, glTexImage2D, GL_TEXTURE_2D, GL_UNSIGNED_BYTE, GL_RGB8, glPixelStorei, GL_UNPACK_ALIGNMENT,
)

import traceback
import imgui

renderer = Renderer()


def main():
    initial_viewport_size = utils.read_window_size_from_imgui_ini("Viewport")
    renderer.init(win_size=glm.ivec2(1024, 768), viewport_size=initial_viewport_size)

    assets = Assets(renderer)
    assets.load_obj("monkey", "models/suzanne_smooth.obj")
    assets.load_obj("ship", "models/ship.obj")
    assets.load_obj("cube", "models/cube.obj")
    assets.load_obj("quad", "models/plane.obj")
    assets.load_obj("sphere", "models/sphere_ico_smooth.obj")
    assets.load_shader("default", "shaders/default.vert", "shaders/default.frag")
    assets.load_shader("fullscreen", "shaders/fullscreen_quad.vert", "shaders/fullscreen_quad.frag")
    assets.make_texture("scene", renderer.get_texdesc_3channel_8bit())
    assets.make_texture("world_pos", renderer.get_texdesc_3channel_flt32())
    assets.make_texture("world_normal", renderer.get_texdesc_3channel_flt32())
    assets.make_texture("uv", renderer.get_texdesc_2channel_flt32())
    assets.make_texture("my_depth", renderer.get_texdesc_1channel_flt32())  # actually a color attachment
    assets.make_texture("mesh_id", renderer.get_texdesc_1channel_int32())
    assets.make_texture("mesh_id_colored", renderer.get_texdesc_3channel_8bit())
    assets.make_texture("viewport", renderer.get_texdesc_3channel_8bit())
    assets.make_texture("cpu", renderer.get_texdesc_3channel_8bit())
    pbo_world_pos = PixelBuffer(initial_viewport_size.x, initial_viewport_size.y, assets.textures["world_pos"].desc.num_channels(), assets.textures["world_pos"].desc.dtype())
    pbo_cpu = PixelBuffer(initial_viewport_size.x, initial_viewport_size.y, assets.textures["cpu"].desc.num_channels(), assets.textures["cpu"].desc.dtype())
    fb_gbuffer = Framebuffer(
        color_textures=[assets.textures[name] for name in ["scene", "world_pos", "world_normal", "uv", "my_depth", "mesh_id", "mesh_id_colored"]],
        depth_texture=Texture(renderer.get_texdesc_default_depth())  # TODO: replace with has_depth, and has_stencil bools default to False
    )
    fb_viewport = Framebuffer([assets.textures["viewport"]])
    
    scene = Scene(renderer)
    scene.clear_color = glm.vec3(0.1, 0.15, 0.2)
    scene.ambient_light.color = glm.vec3(0, 0, 0)
    scene.directional_light.intensity = 0.4
    scene.directional_light.direction = glm.vec3(-2, -1, 0)
    scene.directional_light.color = glm.vec3(165, 218, 55) / 255
    scene.hemispherical_light.intensity = 0.3
    scene.point_lights.append(PointLight(color=glm.vec3(1, 0, 0)))
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
    
    im_windows = ui.ImWindows(assets, scene, viewport_size=initial_viewport_size)

    #globals().update(locals())
    
    while renderer.is_running():
        glfw.poll_events()  # https://github.com/ocornut/imgui/issues/3575 Shouldn't poll events after ImGui starts
        # TODO: separate renderer and ui. Call ui.begin_frame() before renderer.begin_frame() so that renderer gets viewport_size at the same frame, not a frame late
        renderer.imgui_impl.process_inputs()
        imgui.new_frame()  # removes CONFIG_VIEWPORTS_ENABLE from imgui.get_io().config_flags
        utils.imgui_dockspace_over_viewport()        
        im_windows.draw()
        renderer.begin_frame(viewport_size=im_windows.viewport_size, fbos=[fb_gbuffer, fb_viewport], cam=scene.cam)
        assets.textures["cpu"].resize_if_needed(im_windows.viewport_size.x, im_windows.viewport_size.y)
        pbo_world_pos.resize_if_needed(im_windows.viewport_size.x, im_windows.viewport_size.y)
        pbo_cpu.resize_if_needed(im_windows.viewport_size.x, im_windows.viewport_size.y)

        glClearColor(0.1, 0.2, 0.3, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)        
          
        fb_gbuffer.bind()
        # TODO: figure out how to clear scene tex differently then the rest of the color attachments        
        glClearColor(0, 0, 0, 1.0)
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
            scene.directional_light.upload_to_shader(obj.shader)
            scene.hemispherical_light.upload_to_shader(obj.shader)
            for pl in scene.point_lights:
                pl.upload_to_shader(obj.shader)
            glDrawArrays(GL_TRIANGLES, 0, obj.mesh.vertex_count)
            glBindVertexArray(0)
            obj.shader.unbind()
        
        if True:
            assert(assets.textures["world_pos"].desc.width == assets.textures["world_normal"].desc.width)
            assert(assets.textures["world_pos"].desc.width == assets.textures["cpu"].desc.width)
            glReadBuffer(GL_COLOR_ATTACHMENT0 + 1)
            w, h = assets.textures["cpu"].desc.width, assets.textures["cpu"].desc.height
            worldPos = glReadPixels(0, 0, w, h, GL_RGB, GL_FLOAT).reshape(-1, 3)
            glReadBuffer(GL_COLOR_ATTACHMENT0 + 2)
            worldNorm = glReadPixels(0, 0, w, h, GL_RGB, GL_FLOAT).reshape(-1, 3)
            lightPos = np.array([[0, 5, 0]])
            surfToLight = lightPos - worldPos
            lightDir = surfToLight / np.linalg.norm(surfToLight, ord=2, axis=1).reshape(-1, 1)
            dot = np.einsum('ij,ij->i', worldNorm, lightDir).reshape(-1, 1)
            diffuse = np.maximum(0, dot) * 255
            rgb = np.repeat(diffuse, repeats=3, axis=1)
            pixels = np.asarray(rgb, dtype=np.uint8).flatten()
            assets.textures["cpu"].bind()
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, pixels)
            assets.textures["cpu"].unbind()

        # TODO: implement point light via numba+cuda (via copying to pixel buffer)
        # TODO: Make an enum: 1) numpy, 2) numba+cuda.
        # TODO: Measure duration
        if True:
            pbo_world_pos.read_tex(assets.textures["world_pos"])
            pbo_cpu.read_tex(assets.textures["cpu"])
            arr_world_pos = pbo_world_pos.map_as_np_array()
            arr_cpu = pbo_cpu.map_as_np_array()
            # arr_cpu[:, :, :] = np.asarray(arr_world_pos * 255.99, dtype=np.uint8)
            arr_cpu[:, :, 0] = 255
            pbo_world_pos.unmap()
            pbo_cpu.unmap()
            pbo_cpu.write_tex(assets.textures["cpu"])
        fb_gbuffer.unbind()


        fb_viewport.bind()
        glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glActiveTexture(GL_TEXTURE0 + 0)
        assets.textures["scene"].bind()
        glActiveTexture(GL_TEXTURE0 + 1)
        assets.textures["world_pos"].bind()
        glActiveTexture(GL_TEXTURE0 + 2)
        assets.textures["world_normal"].bind()
        glActiveTexture(GL_TEXTURE0 + 3)
        assets.textures["uv"].bind()
        glActiveTexture(GL_TEXTURE0 + 4)
        assets.textures["mesh_id"].bind()        
        fullscreen_shader = assets.shaders["fullscreen"]
        fullscreen_shader.bind()
        fullscreen_shader.set_uniform_vec3("eyePos", scene.cam.position)
        scene.ambient_light.upload_to_shader(fullscreen_shader)
        scene.directional_light.upload_to_shader(fullscreen_shader)
        scene.hemispherical_light.upload_to_shader(fullscreen_shader)
        for pl in scene.point_lights:
            pl.upload_to_shader(fullscreen_shader)        
        glBindVertexArray(renderer.empty_vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        fullscreen_shader.unbind()
        fb_viewport.unbind()
    
        renderer.end_frame()
        
    renderer.deinit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        renderer.deinit()