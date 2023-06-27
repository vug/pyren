from texture import Texture, TextureDescription

import glfw
import glm
import imgui
from imgui.integrations.glfw import GlfwRenderer
import numpy as np
from OpenGL.GL import GL_FALSE, GL_FLOAT, GL_INT
# Texture related imports
from OpenGL.GL import GL_DEPTH_COMPONENT, GL_DEPTH_COMPONENT32
from OpenGL.GL import GL_RGB, GL_RGB8, GL_UNSIGNED_BYTE, GL_RGB32F
from OpenGL.GL import GL_RG, GL_RG32F
from OpenGL.GL import GL_R32I, GL_RED_INTEGER
# Shader related imports
from OpenGL.GL import GL_COMPILE_STATUS, GL_FRAGMENT_SHADER, GL_LINK_STATUS, GL_VERTEX_SHADER, glAttachShader, glCompileShader, glCreateProgram, glCreateShader, glDeleteShader, glDetachShader, glGetProgramiv, glGetShaderiv, glGetShaderInfoLog, glGetUniformLocation, glLinkProgram, glShaderSource, glUniform1i, glUniform3fv, glUniformMatrix4fv, glUseProgram
# OpenGL queries realted imports
from OpenGL.GL import GL_MAX_COLOR_ATTACHMENTS, GL_SHADING_LANGUAGE_VERSION, GL_RENDERER, GL_VERSION, glGetIntegerv, glGetString
# Graphics pipeline settings related imports
from OpenGL.GL import GL_CULL_FACE, GL_DEPTH_TEST, glEnable
from OpenGL.GL import GL_BACK, glCullFace
from OpenGL.GL import GL_LESS, glDepthFunc
# Geometry/Mesh related imports
from OpenGL.GL import GL_ARRAY_BUFFER, GL_STATIC_DRAW, glBindBuffer, glBindVertexArray, glBufferData, glEnableVertexAttribArray, glGenBuffers, glGenVertexArrays, glVertexAttribPointer

import ctypes


# TODO: renderer.make_default_framebuffer(colors=None, has_depth: bool, has_stencil: bool):
# creates textures same size as window
# if colors is None, one color attachment of screensize with RGBA8


class Mesh:
    def __init__(self, vao, vertex_count):
        self.vao = vao;
        self.vertex_count = vertex_count


class Shader:
    def __init__(self, vertex_file, fragment_file):
        self.vertex_file = vertex_file
        self.fragment_file = fragment_file

        self._id = glCreateProgram()
        self._vert_id = -1
        self._frag_id = -1
        self._vert_src = ""
        self._frag_src = ""

        self.__load()
        self.__compile()

    def get_id(self):
        return self._id

    def get_vert_id(self):
        return self._vert_id

    def get_frag_id(self):
        return self._frag_id

    def get_vertex_src(self):
        return self._vertex_src

    def get_frag_src(self):
        return self._frag_src

    def reload(self):
        self.__load()
        self.__compile()

    def is_valid(self):
        return glGetProgramiv(self._id, GL_LINK_STATUS)

    def bind(self):
        assert(self.is_valid())
        glUseProgram(self._id)

    def unbind(self):
        glUseProgram(0)

    def set_uniform_int1(self, name, val):
      loc = glGetUniformLocation(self._id, name)
      glUniform1i(loc, val)

    def set_uniform_vec3(self, name, val):
        loc = glGetUniformLocation(self._id, name)
        glUniform3fv(loc, 1, glm.value_ptr(val))

    def set_uniform_mat4(self, name, val):
        loc = glGetUniformLocation(self._id, name)
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(val))


    def __load(self):
        with open(self.vertex_file, 'r') as file:
            self._vert_src = file.read()
        with open(self.fragment_file, 'r') as file:
            self._frag_src = file.read()

    def __compile(self):
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, [self._vert_src], None)  # TODO: try non-array
        glCompileShader(vs)
        status = glGetShaderiv(vs, GL_COMPILE_STATUS)
        if status != 1:
            print('VERTEX SHADER ERROR')
            print(glGetShaderInfoLog(vs).decode())
            glDeleteShader(vs)
            return -1

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, [self._frag_src], None)
        glCompileShader(fs)
        status = glGetShaderiv(fs, GL_COMPILE_STATUS)
        if status != 1:
            print('FRAGMENT SHADER ERROR')
            print(glGetShaderInfoLog(fs).decode())
            glDeleteShader(vs)
            glDeleteShader(fs)
            return -1

        if self.is_valid():
            glDetachShader(self.get_id(), self.get_vert_id());
            glDetachShader(self.get_id(), self.get_frag_id());

        glAttachShader(self.get_id(), vs)
        glAttachShader(self.get_id(), fs)
        glLinkProgram(self.get_id())
        status = glGetProgramiv(self.get_id(), GL_LINK_STATUS)
        if status != 1:
            print('status', status)
            print('SHADER PROGRAM', glGetShaderInfoLog(self._id))
            glDeleteShader(vs)
            glDeleteShader(fs)
            return -1

        self._vert_id = vs
        self._frag_id = fs

        # glDeleteShader(vs)
        # glDeleteShader(fs)

        return self.get_id()


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

class Renderer:
    def init(self):
        self._has_frame_begun = False
        glfw.init()  # without hints chooses v4.6 anyway
        self.win_size = glm.ivec2(800, 600)
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


    # TODO: move into Mesh class constructor
    def create_mesh_buffer(self, np_vertices):
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)
        vbo = glGenBuffers(1)
        print(f"vao {vao}, vbo {vbo}")
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, np_vertices, GL_STATIC_DRAW)
        offset = 0
        # pos 3, tex 2, nrm 3, col 4
        sizes = [3, 2, 3, 4]
        vertex_size = sum(sizes)
        for ix, size in enumerate(sizes):
            stride = vertex_size * np.dtype('float32').itemsize
            offset_ptr = ctypes.c_void_p(offset * np.dtype('float32').itemsize)
            glVertexAttribPointer(ix, size, GL_FLOAT, GL_FALSE, stride, offset_ptr)
            glEnableVertexAttribArray(ix)
            # print(f"vertex attribute[{ix}]: {attrib}, size: {size}, offset: {offset}, stride: {stride}")
            offset += size
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        assert(len(np_vertices) / vertex_size % 3 == 0)
        mesh = Mesh(vao, len(np_vertices) // vertex_size)
        return mesh

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

def pointer_offset(n=0):
    return ctypes.c_void_p(4 * n)
