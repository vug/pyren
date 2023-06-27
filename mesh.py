import numpy as np
from OpenGL.GL import GL_STATIC_DRAW, glBindBuffer, glBufferData, glGenBuffers
from OpenGL.GL import glBindVertexArray, GL_ARRAY_BUFFER, glGenVertexArrays
from OpenGL.GL import glEnableVertexAttribArray, glVertexAttribPointer
from OpenGL.GL import GL_FLOAT, GL_FALSE

import ctypes

class Mesh:
    def __init__(self, np_vertices):
        self.vao = glGenVertexArrays(1)

        glBindVertexArray(self.vao)
        vbo = glGenBuffers(1)
        print(f"vao {self.vao}, vbo {vbo}")
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
        self.vertex_count = len(np_vertices) // vertex_size

def pointer_offset(n=0):
    return ctypes.c_void_p(4 * n)
