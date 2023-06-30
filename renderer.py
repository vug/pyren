from texture import Texture, TextureDescription

import glfw
import glm
import imgui
from imgui.integrations.glfw import GlfwRenderer
import numpy as np
from OpenGL.GL import GL_FLOAT, GL_INT
# Texture related imports
from OpenGL.GL import GL_DEPTH_COMPONENT, GL_DEPTH_COMPONENT32
from OpenGL.GL import GL_RGB, GL_RGB8, GL_UNSIGNED_BYTE, GL_RGB32F
from OpenGL.GL import GL_RED, GL_R32F, GL_RG, GL_RG32F
from OpenGL.GL import GL_R32I, GL_RED_INTEGER
# OpenGL queries realted imports
from OpenGL.GL import GL_MAX_COLOR_ATTACHMENTS, GL_SHADING_LANGUAGE_VERSION, GL_RENDERER, GL_VERSION, glGetIntegerv, glGetString
# Graphics pipeline settings related imports
from OpenGL.GL import GL_CULL_FACE, GL_DEPTH_TEST, glEnable
from OpenGL.GL import GL_BACK, glCullFace
from OpenGL.GL import GL_LESS, glDepthFunc

# TODO: renderer.make_default_framebuffer(colors=None, has_depth: bool, has_stencil: bool):
# creates textures same size as window
# if colors is None, one color attachment of screensize with RGBA8


class Renderer:
    def init(self, width=800, height=600):
        self._has_frame_begun = False
        glfw.init()  # without hints chooses v4.6 anyway
        self.win_size = glm.ivec2(width, 600)
        self.window = glfw.create_window(self.win_size.x, self.win_size.y, "Hello World", None, None)
        # initialize openGL context before calling any gl functions such as `glGenVertexArrays`
        # otherwise it's expecting old API, or cumbersome workarounds such as https://github.com/tartley/gltutpy/blob/master/t01.hello-triangle/glwrap.py
        glfw.make_context_current(self.window)
        print(f"OpenGL info: version {glGetString(GL_VERSION)}, renderer {glGetString(GL_RENDERER)}, GLSL version {glGetString(GL_SHADING_LANGUAGE_VERSION)}, max col attach {glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS)}")

        imgui.create_context()
        self.imgui_impl = GlfwRenderer(self.window)
        imgui.get_io().display_size = self.win_size.x, self.win_size.y

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

    def deinit(self):
        # due to some error we were not able to call imgui.end_frame()
        if self._has_frame_begun:
            imgui.end_frame()
        self.imgui_impl.shutdown()
        glfw.terminate()

    def is_running(self):
        return not glfw.window_should_close(self.window)

    def begin_frame(self):
        glfw.poll_events()
        (w, h) = glfw.get_window_size(self.window)
        self.win_size.x = w
        self.win_size.y = h
        self.imgui_impl.process_inputs()
        imgui.new_frame()
        self._has_frame_begun = True

    def end_frame(self):
        imgui.render()
        self.imgui_impl.render(imgui.get_draw_data())
        imgui.end_frame()
        glfw.swap_buffers(self.window)
        self._has_frame_begun = False

    def make_default_color_tex(self):
        return self.make_tex_three_channel_8bit()

    def make_default_depth_tex(self):
        return self.make_tex_depth32()

    def make_tex_3channel_8bit(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_RGB8,
            format=GL_RGB,
            type=GL_UNSIGNED_BYTE,
        )
        return Texture(desc)

    def make_tex_3channel_flt32(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_RGB32F,
            format=GL_RGB,
            type=GL_FLOAT,
        )
        return Texture(desc)

    def make_tex_2channel_flt32(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_RG32F,
            format=GL_RG,
            type=GL_FLOAT,
        )
        return Texture(desc)
    
    def make_tex_1channel_flt32(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_R32F,
            format=GL_RED,
            type=GL_FLOAT,
        )
        return Texture(desc)        

    def make_tex_1channel_int32(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_R32I,
            format=GL_RED_INTEGER,
            type=GL_INT,
        )
        return Texture(desc)

    def make_tex_depth32(self):
        desc = TextureDescription(
            width=self.win_size.x, height=self.win_size.y,
            internal_format=GL_DEPTH_COMPONENT32,
            format=GL_DEPTH_COMPONENT,
            type=GL_FLOAT
        )
        return Texture(desc)
