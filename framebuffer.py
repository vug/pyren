from texture import Texture

from OpenGL.GL import GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT, GL_STENCIL_ATTACHMENT
from OpenGL.GL import GL_DRAW_FRAMEBUFFER, GL_FRAMEBUFFER
from OpenGL.GL import GL_FRAMEBUFFER_COMPLETE, glCheckFramebufferStatus
from OpenGL.GL import glBindFramebuffer, glDrawBuffers, glFramebufferTexture2D, glGenFramebuffers
from OpenGL.GL import GL_TEXTURE_2D


class Framebuffer:
    def __init__(self, color_textures:[Texture], depth_texture: Texture=None, stencil_texture: Texture=None):
        self._id = glGenFramebuffers(1)
        self.color_textures = color_textures
        self.depth_texture = depth_texture
        self.stencil_texture = stencil_texture
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._id)
        draw_buffers = []
        for n, color_texture in enumerate(color_textures):
            attachment = GL_COLOR_ATTACHMENT0 + n
            glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, GL_TEXTURE_2D, color_texture.get_id(), 0)
            draw_buffers.append(attachment)
        glDrawBuffers(len(draw_buffers), draw_buffers)
        if depth_texture:
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_texture.get_id(), 0)
        if stencil_texture:
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_STENCIL_ATTACHMENT, GL_TEXTURE_2D, stencil_texture.get_id(), 0)

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        assert status == GL_FRAMEBUFFER_COMPLETE, f"Framebuffer error, status: 0x{status:x}"

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def get_id(self) -> int:
        return self._id

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self._id)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def resize_if_needed(self, width: int, height: int):
        for tex in self.color_textures:
            tex.resize_if_needed(width, height)
        if self.depth_texture:
            self.depth_texture.resize_if_needed(width, height)
        if self.stencil_texture:
            self.stencil_texture.resize_if_needed(width, height)