from more_itertools import flatten
import numpy as np
from OpenGL.GL import GL_UNSIGNED_BYTE
from OpenGL.GL import GL_RGBA, GL_RGBA8
from OpenGL.GL import GL_TEXTURE_2D, GL_NEAREST, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER
from OpenGL.GL import GLint, GLenum
from OpenGL.GL import glBindTexture, glGenTextures, glTexImage2D, glTexParameteri

from dataclasses import dataclass

@dataclass
class TextureDescription:
    width: int = 128
    height: int = 128
    # bits of channels, signedness etc. https://docs.gl/gl4/glTexImage2D
    internal_format: GLint = GL_RGBA8
    # Which channels
    format: GLenum = GL_RGBA
    type: GLenum = GL_UNSIGNED_BYTE
    min_filter: GLint = GL_NEAREST
    mag_filter: GLint = GL_NEAREST


class Texture:
    def __init__(self, desc: TextureDescription, data = None):
        self.desc = desc
        self.data = data
        self._id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, desc.min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, desc.mag_filter)
        glTexImage2D(GL_TEXTURE_2D, 0, desc.internal_format, desc.width, desc.height, 0, desc.format, desc.type, data)
        glBindTexture(GL_TEXTURE_2D, 0)

    def get_id(self) -> int:
        return self._id

    def set_data(self, data):
        self.data = data
        self.bind()
        glTexImage2D(GL_TEXTURE_2D, 0, self.desc.internal_format, self.desc.width, self.desc.height, 0, self.desc.format, self.desc.type, self.data)
        self.unbind()

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self._id)

    def unbind(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def resize_if_needed(self, width: int, height: int):
        if (self.desc.width == width and self.desc.height == height):
            return
        self.desc.width = width
        self.desc.height = height
        self.bind()
        glTexImage2D(GL_TEXTURE_2D, 0, self.desc.internal_format, self.desc.width, self.desc.height, 0, self.desc.format, self.desc.type, None)
        self.unbind()

    def create_example_texture():
        texDesc = TextureDescription()
        texData = np.array(list(flatten([[i, j, 128, 255] for i in range(texDesc.height) for j in range(texDesc.width)])))
        return Texture(texDesc, texData)
