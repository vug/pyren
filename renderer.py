from camera import Camera
from texture import TextureDescription
from framebuffer import Framebuffer
import utils

import glfw
import glm
import imgui
from imgui.integrations.glfw import GlfwRenderer
from OpenGL.GL import GL_FLOAT, GL_INT, glGenVertexArrays
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
from OpenGL.GL import GL_MAX_UNIFORM_LOCATIONS, GL_MAX_FRAGMENT_UNIFORM_COMPONENTS, GL_MAX_FRAGMENT_UNIFORM_VECTORS, GL_MAX_FRAGMENT_UNIFORM_BLOCKS
#
from OpenGL.GL import glViewport


class Renderer:
    def init(self, win_size: glm.ivec2, viewport_size: glm.ivec2):
        self.win_size = win_size
        self.viewport_size = viewport_size
        self._has_frame_begun = False
        glfw.init()  # without hints chooses v4.6 anyway
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        # glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_COMPAT_PROFILE)
        # glfw.window_hint(glfw.SAMPLES, 4)
        # glfw.window_hint(glfw.OPENGL_DEBUG_CONTEXT, True)  # TODO: bring debug context
        self.window = glfw.create_window(self.win_size.x, self.win_size.y, "PyRen", None, None)
        # initialize openGL context before calling any gl functions such as `glGenVertexArrays`
        # otherwise it's expecting old API, or cumbersome workarounds such as https://github.com/tartley/gltutpy/blob/master/t01.hello-triangle/glwrap.py
        glfw.make_context_current(self.window)
        print(f"OpenGL info: version {glGetString(GL_VERSION)}, renderer {glGetString(GL_RENDERER)}, GLSL version {glGetString(GL_SHADING_LANGUAGE_VERSION)}\n"
              f"GL_MAX_COLOR_ATTACHMENTS {glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS)}\n"
              f"GL_MAX_UNIFORM_LOCATIONS {glGetIntegerv(GL_MAX_UNIFORM_LOCATIONS)}\n"
              f"GL_MAX_FRAGMENT_UNIFORM_COMPONENTS {glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_COMPONENTS)}, GL_MAX_FRAGMENT_UNIFORM_VECTORS {glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_VECTORS)}\n"
              f"GL_MAX_FRAGMENT_UNIFORM_BLOCKS {glGetIntegerv(GL_MAX_FRAGMENT_UNIFORM_BLOCKS)}\n"
        )

        imgui.create_context()
        io = imgui.get_io()
        io.display_size = self.win_size.x, self.win_size.y
        io.config_flags |= imgui.CONFIG_NAV_ENABLE_KEYBOARD
        # io.config_flags |= imgui.CONFIG_VIEWPORTS_ENABLE  # Not working at the moment. See below.
        io.config_flags |= imgui.CONFIG_DOCKING_ENABLE
        io.config_windows_move_from_title_bar_only = True
        self.imgui_impl = GlfwRenderer(self.window)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        self.empty_vao = glGenVertexArrays(1)

    def deinit(self):
        # due to some error we were not able to call imgui.end_frame()
        if self._has_frame_begun:
            imgui.end_frame()
        self.imgui_impl.shutdown()
        glfw.terminate()

    def is_running(self):
        return not glfw.window_should_close(self.window)

    def begin_frame(self, viewport_size: glm.ivec2, fbos: list[Framebuffer], cam: Camera):
        """
        viewport_size: ivec2 size of the "Viewport" ImWindow in which the final render is displayed
        fbos: Framebuffers registered to the renderer that'll be resized to the given viewport_size
        cam: Camera whose aspect ratio will be updated according to viewport aspect ratio
        """        
        self.viewport_size = viewport_size
        glfw.poll_events()
        (w, h) = glfw.get_window_size(self.window)
        self.win_size = glm.ivec2(w, h)
        self.imgui_impl.process_inputs()
        imgui.new_frame()  # removes CONFIG_VIEWPORTS_ENABLE from imgui.get_io().config_flags
        utils.imgui_dockspace_over_viewport()
        for fb in fbos:
            fb.resize_if_needed(self.viewport_size.x, self.viewport_size.y)
        cam.aspect_ratio = self.viewport_size.x / self.viewport_size.y
        glViewport(0, 0, self.viewport_size.x, self.viewport_size.y)
        self._has_frame_begun = True


    def end_frame(self):
        imgui.render()
        self.imgui_impl.render(imgui.get_draw_data())

        # CONFIG_VIEWPORTS_ENABLE is removed from imgui.get_io().config_flags at imgui.new_frame()
        # also render_platform_windows_default() has not been implemented yet https://github.com/pyimgui/pyimgui/issues/259#issuecomment-1039239640
        if (imgui.get_io().config_flags & imgui.CONFIG_VIEWPORTS_ENABLE):
            context = glfw.get_current_context()
            imgui.update_platform_windows()
            imgui.render_platform_windows_default()
            glfw.make_context_current(context)

        # imgui.end_frame()
        glfw.swap_buffers(self.window)
        self._has_frame_begun = False

    def get_texdesc_default_color(self) -> TextureDescription:
        return self.get_texdesc_3channel_8bit()

    def get_texdesc_default_depth(self) -> TextureDescription:
        return self.get_texdesc_depth32()

    def get_texdesc_3channel_8bit(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_RGB8,
            format=GL_RGB,
            type=GL_UNSIGNED_BYTE,
        )
        return desc

    def get_texdesc_3channel_flt32(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_RGB32F,
            format=GL_RGB,
            type=GL_FLOAT,
        )
        return desc

    def get_texdesc_2channel_flt32(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_RG32F,
            format=GL_RG,
            type=GL_FLOAT,
        )
        return desc
    
    def get_texdesc_1channel_flt32(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_R32F,
            format=GL_RED,
            type=GL_FLOAT,
        )
        return desc

    def get_texdesc_1channel_int32(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_R32I,
            format=GL_RED_INTEGER,
            type=GL_INT,
        )
        return desc

    def get_texdesc_depth32(self) -> TextureDescription:
        desc = TextureDescription(
            width=self.viewport_size.x, height=self.viewport_size.y,
            internal_format=GL_DEPTH_COMPONENT32,
            format=GL_DEPTH_COMPONENT,
            type=GL_FLOAT
        )
        return desc
