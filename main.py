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
from lights import PointLight
import renderer as rndr
from scene import Scene, Object
from texture import Texture
import ui
import utils

import glm
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear, glClearColor,
    GL_TRIANGLES, glBindVertexArray, glDrawArrays,
    glActiveTexture, GL_TEXTURE0, glViewport
)

import traceback

renderer = rndr.Renderer()

def main():   
    renderer.init(1024, 768)

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
    fb = Framebuffer(
        color_textures=[assets.textures[name] for name in ["scene", "world_pos", "world_normal", "uv", "my_depth", "mesh_id", "mesh_id_colored"]],
        depth_texture=Texture(renderer.get_texdesc_default_depth())  # TODO: replace with has_depth, and has_stencil bools default to None
    )    
    
    scene = Scene(renderer)
    scene.clear_color = glm.vec3([0.1, 0.15, 0.2])
    scene.ambient_light.color = glm.vec3(0, 0, 0)
    scene.directional_light.intensity = 0.4
    scene.directional_light.direction = glm.vec3([-2, -1, 0])
    scene.directional_light.color = glm.vec3([165, 218, 55]) / 255
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
    
    im_windows = ui.ImWindows(assets, scene)

    #globals().update(locals())
    
    while renderer.is_running():
        renderer.begin_frame()
        fb.resize_if_needed(renderer.win_size.x, renderer.win_size.y)
        scene.cam.aspect_ratio = renderer.win_size.x / renderer.win_size.y
        glViewport(0, 0, renderer.win_size.x, renderer.win_size.y)
        
        im_windows.draw()
          
        fb.bind()
        # TODO: scene has a clear method `clear(color=True, depth=True)`
        # glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1.0)
        # glClearTexImage(fb.color_textures[0].get_id(), 0, fb.color_textures[0].desc.format, fb.color_textures[0].desc.type, glm.value_ptr(scene.clear_color))
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
        fb.unbind()

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
        
        # Clear editor background
        glClearColor(scene.clear_color.r, scene.clear_color.g, scene.clear_color.b, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        fullscreen_shader = assets.shaders["fullscreen"]
        fullscreen_shader.bind()
        fullscreen_shader.set_uniform_vec3("eyePos", scene.cam.position)
        scene.ambient_light.upload_to_shader(fullscreen_shader)
        scene.directional_light.upload_to_shader(fullscreen_shader)
        scene.hemispherical_light.upload_to_shader(fullscreen_shader)
        for pl in scene.point_lights:
            pl.upload_to_shader(obj.shader)        
        glBindVertexArray(renderer.empty_vao)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        fullscreen_shader.unbind()      
    
        renderer.end_frame()
        
    renderer.deinit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        renderer.deinit()