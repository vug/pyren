import ctypes
from dataclasses import dataclass

from more_itertools import flatten
import numpy as np
from OpenGL.GL import GL_UNSIGNED_BYTE, GLubyte, GLfloat
from OpenGL.GL import GL_RED, GL_RED_INTEGER, GL_RG, GL_RGB, GL_RGBA, GL_RGBA8, GL_FLOAT, GL_RGB32F, GL_RG32F, GL_R32F, GL_INT, GL_R32I
from OpenGL.GL import GL_TEXTURE_2D, GL_NEAREST, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER
from OpenGL.GL import GLint, GLenum
from OpenGL.GL import glBindTexture, glGenTextures, glTexImage2D, glTexParameteri
from OpenGL.GL import glGenBuffers, glBindBuffer, glBufferData, GL_PIXEL_PACK_BUFFER, GL_PIXEL_UNPACK_BUFFER, glTexSubImage2D, GL_STREAM_DRAW, glGetTextureImage, glMapBuffer, glUnmapBuffer, GL_READ_ONLY
from OpenGL.GL import glGetTexLevelParameteriv, glGetTextureLevelParameteriv, GL_TEXTURE_BUFFER_SIZE
from OpenGL.GL import arrays, GL_TEXTURE_WIDTH, GL_TEXTURE_HEIGHT, GL_TEXTURE_DEPTH, GL_TEXTURE_INTERNAL_FORMAT, GL_TEXTURE_RED_SIZE, GL_TEXTURE_GREEN_SIZE, GL_TEXTURE_BLUE_SIZE, GL_TEXTURE_ALPHA_SIZE

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

    def num_channels(self) -> int:
        if self.format == GL_RGBA:
            return 4
        if self.format == GL_RGB:
            return 3
        if self.format == GL_RG:
            return 2
        if self.format == GL_RED or self.format == GL_RED_INTEGER:
            return 1
        else:
            raise NotImplementedError("TODO: Implement num_channels for other formats!")
    
    def dtype(self) -> np.dtype:
        # Probably I'll only use 32-bit floats and integers
        if self.type == GL_FLOAT:
            assert(self.internal_format in (GL_RGB32F, GL_RG32F, GL_R32F))
            return np.dtype(np.float32)
        if self.type == GL_INT:
            assert(self.internal_format in (GL_R32I, ))
            return np.dtype(np.int32)
        if self.type == GL_UNSIGNED_BYTE:
            return np.dtype(np.uint8)
        else:
            raise NotImplementedError("TODO: Implement dtype for other types")
    
    def pixel_size(self) -> int:
        return self.num_channels() * self.dtype().itemsize
    
    def size_in_bytes(self) -> int:
        return self.width * self.height * self.pixel_size()


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
    
    def fill_with_zeros(self):
        data = np.zeros(shape=(self.desc.width, self.desc.height, self.desc.num_channels()), dtype=self.desc.dtype())
        self.set_data(data)

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
    
    def debug(self):
        self.bind()
        tex_width = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH)
        tex_height = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT)
        tex_depth = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_DEPTH)
        tex_internal_format = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_INTERNAL_FORMAT)
        tex_red_size = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_RED_SIZE)
        tex_green_size = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_GREEN_SIZE)
        tex_blue_size = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_BLUE_SIZE)
        tex_alpha_size = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_ALPHA_SIZE)
        self.unbind()
        # TODO: add GL_TEXTURE_BUFFER_OFFSET, GL_TEXTURE_BUFFER_SIZE


class PixelBuffer:
    def __init__(self, width: int, height: int, num_channels: int, dtype: np.dtype):
        self._id = glGenBuffers(1)
        self.width = width
        self.height = height
        self.num_channels = num_channels
        self.dtype = dtype
        self.size_in_bytes = 0
    
    def read_tex(self, tex: Texture):
        desc = tex.desc
        assert self.width == desc.width and self.height == desc.height
        assert self.num_channels == desc.num_channels() and self.dtype == desc.dtype()
        self.size_in_bytes = desc.size_in_bytes()
        glBindBuffer(GL_PIXEL_PACK_BUFFER, self._id)
        glBufferData(GL_PIXEL_PACK_BUFFER, self.size_in_bytes, None, GL_STREAM_DRAW)  # assuming will update every frame
        glGetTextureImage(tex.get_id(), 0, desc.format, desc.type, self.size_in_bytes, ctypes.c_void_p(0))
        glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)
    
    def write_tex(self, tex: Texture):
        desc = tex.desc
        assert self.width == desc.width and self.height == desc.height
        assert self.num_channels == desc.num_channels() and self.dtype == desc.dtype()
        assert self.size_in_bytes > 0
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, self._id)
        glBindTexture(GL_TEXTURE_2D, tex.get_id())
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, desc.width, desc.height, desc.format, desc.type, ctypes.c_void_p(0))
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)

    def resize_if_needed(self, width: int, height: int) -> bool:
        if (self.width == width and self.height == height):
            return False
        glBindBuffer(GL_PIXEL_PACK_BUFFER, self._id)
        glBufferData(GL_PIXEL_PACK_BUFFER, width * height * self.num_channels * self.dtype.itemsize, None, GL_STREAM_DRAW)
        glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)
        self.width, self.height = width, height
        return True
    
    def map_as_np_array(self):
        glBindBuffer(GL_PIXEL_PACK_BUFFER, self._id)
        pixels_ptr = glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY)
        ctype = GLubyte
        if self.dtype == np.uint8:
            ctype = GLubyte
        elif self.dtype == np.float32:
            ctype = GLfloat
        else:
            raise NotImplementedError("Add ctype for given dtype")
        map_array_ctype = (ctype * self.width * self.height * self.num_channels).from_address(pixels_ptr)
        map_array = np.ctypeslib.as_array(map_array_ctype).reshape((self.width, self.height, self.num_channels))
        glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)
        return map_array
    
    def unmap_as_np_array(self):
        glBindBuffer(GL_PIXEL_PACK_BUFFER, self._id)
        glUnmapBuffer(GL_PIXEL_PACK_BUFFER)
        glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)
    
    def get_id(self) -> int:
        return self._id

    def deinit(self):
        raise NotImplementedError("Delete PBO")

