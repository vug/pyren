import glm
# Shader related imports
from OpenGL.GL import GL_FALSE
from OpenGL.GL import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, glCompileShader, glCreateShader, glDeleteShader, glDetachShader, glGetShaderiv, glGetShaderInfoLog, glGetProgramInfoLog
from OpenGL.GL import glGetUniformLocation, glUniform1i, glUniform1f, glUniform3fv, glUniformMatrix4fv
from OpenGL.GL import GL_COMPILE_STATUS, GL_LINK_STATUS, glAttachShader, glCreateProgram, glGetProgramiv, glLinkProgram, glShaderSource, glUseProgram, GL_INFO_LOG_LENGTH
from OpenGL.GL import glShaderBinary, glSpecializeShader, GL_SHADER_BINARY_FORMAT_SPIR_V, glProgramUniformMatrix4fv, glGetShaderSource
import pyshaderc

class Shader:
    def __init__(self, vertex_file, fragment_file, use_spirv=True):
        self.vertex_file = vertex_file
        self.fragment_file = fragment_file

        self._id = glCreateProgram()
        self._vert_id = -1
        self._frag_id = -1
        self._vert_src = ""
        self._frag_src = ""
        self.use_spirv = use_spirv

        if not self.use_spirv:
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
        if not self.use_spirv:
            self.__load()
        return self.__compile()

    def is_valid(self):
        return glGetProgramiv(self._id, GL_LINK_STATUS)

    def bind(self):
        # usually triggered when shader already has errors before app start
        assert self.is_valid(), f"Shader ({self.vertex_file}, {self.fragment_file}) is not valid."
        glUseProgram(self._id)

    def unbind(self):
        glUseProgram(0)

    def set_uniform_int1(self, name, val):
      loc = glGetUniformLocation(self._id, name)
      glUniform1i(loc, val)

    def set_uniform_float1(self, name, val):
      loc = glGetUniformLocation(self._id, name)
      glUniform1f(loc, val)

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
    
    def __compile_file_into_spirv(self, shader_id, filepath, stage):
        try:
            spirv_bytes = pyshaderc.compile_file_into_spirv(filepath, stage, optimization='zero')
            glShaderBinary(1, shader_id, GL_SHADER_BINARY_FORMAT_SPIR_V, spirv_bytes, len(spirv_bytes))
            glSpecializeShader(shader_id, 'main', 0, None, None)
        except pyshaderc.CompilationError as ce:
            print("[ERROR] ShaderC SPIRV Compilation Error: ", str(ce))

    def __compile(self):
        vs = glCreateShader(GL_VERTEX_SHADER)
        if self.use_spirv:
            self.__compile_file_into_spirv(vs, self.vertex_file, 'vert')
        else:
            glShaderSource(vs, [self._vert_src], None)  # TODO: try non-array
            glCompileShader(vs)
        status = glGetShaderiv(vs, GL_COMPILE_STATUS)
        if status != 1:
            print(f"[ERROR] Vertex shader compilation with status {status}")
            print(glGetShaderInfoLog(vs))
            glDeleteShader(vs)
            return -1

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        if self.use_spirv:
            self.__compile_file_into_spirv(fs, self.fragment_file, 'frag')
        else:
            glShaderSource(fs, [self._frag_src], None)
            glCompileShader(fs)
        status = glGetShaderiv(fs, GL_COMPILE_STATUS)
        if status != 1:
            print(f"[ERROR] Fragment shader compilation with status {status}")
            print(glGetShaderInfoLog(fs))
            glDeleteShader(vs)
            glDeleteShader(fs)
            return -1

        if self.is_valid():
            glDetachShader(self.get_id(), self.get_vert_id())
            glDetachShader(self.get_id(), self.get_frag_id())

        glAttachShader(self.get_id(), vs)
        glAttachShader(self.get_id(), fs)
        glLinkProgram(self.get_id())
        status = glGetProgramiv(self.get_id(), GL_LINK_STATUS)
        if status != 1:
            print(f"[ERROR] Shader linking failed with status {status}")
            print(glGetProgramInfoLog(self.get_id()))
            glDeleteShader(vs)
            glDeleteShader(fs)
            return -1

        self._vert_id = vs
        self._frag_id = fs

        # glDeleteShader(vs)
        # glDeleteShader(fs)

        return self.get_id()