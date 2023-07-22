from cuda import cudart
import glfw
from more_itertools import flatten
import numba.cuda as nbcuda
import numpy as np
from OpenGL.GL import (
    GLubyte,
    glViewport, glClearColor, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_NEAREST, GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE, glGetTextureImage, GL_TEXTURE_WRAP_S, GL_REPEAT,GL_TEXTURE_WRAP_T, glTexSubImage2D,
    glGenBuffers, glBindBuffer, GL_PIXEL_PACK_BUFFER, glBufferData, GL_STREAM_DRAW, glMapBuffer, GL_READ_ONLY, glUnmapBuffer, GL_PIXEL_UNPACK_BUFFER
)
import OpenGL.GL as GL

import ctypes
import math
import png


# @nbcuda.jit
# def process_pixels(pixels):
#     i, j, k = nbcuda.grid(3)
#     if (i == 0 and j == 0 and k == 3):
#         print("Hi from kernel!", pixels[i, j, 0], pixels[i, j, 1], pixels[i, j, 2], pixels[i, j, 3])
#     # pixels[i, j, k] = 128
#     if k == 0:
#         pixels[i, j, k] = 255 - pixels[i, j, k]
#     if (i == 0 and j == 0 and k == 3):
#         print("Bye from kernel!", pixels[i, j, 0], pixels[i, j, 1], pixels[i, j, 2], pixels[i, j, 3])
    
@nbcuda.jit
def process_pixels(pixels):
    i, j = nbcuda.grid(2)
    if (i == 0 and j == 0):
        print("Hi from 2D kernel!", pixels[i, j, 0], pixels[i, j, 1], pixels[i, j, 2], pixels[i, j, 3])
    pixels[i, j, 0] = 255 - pixels[i, j, 0]
    if (i == 0 and j == 0):
        print("Bye from 2D kernel!", pixels[i, j, 0], pixels[i, j, 1], pixels[i, j, 2], pixels[i, j, 3])

glfw.init()  # without hints chooses v4.6 anyway
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(1024, 768, "Interop", None, None)
glfw.make_context_current(window)
print(f"OpenGL info: version {GL.glGetString(GL.GL_VERSION)}, renderer {GL.glGetString(GL.GL_RENDERER)}, GLSL version {GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)}\n")

# Create texture, fill with initial data
tex_id = glGenTextures(1)
tex_width, tex_height, tex_channels = 512, 512, 4
tex_format, tex_type = GL_RGBA, GL_UNSIGNED_BYTE
glBindTexture(GL_TEXTURE_2D, tex_id)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
tex_init_data = texData = np.array(list(flatten([[i / tex_width * 255.99, j / tex_height * 255.99, 128, 255] for i in range(tex_width) for j in range(tex_height)])), dtype=np.uint8)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, tex_width, tex_height, 0, tex_format, tex_type, tex_init_data)
glBindTexture(GL_TEXTURE_2D, 0)
print(f"tex_id {tex_id}")

# Write Texture into PNG
pixels = np.empty(shape=(tex_width, tex_height, tex_channels), dtype=np.uint8)
glGetTextureImage(tex_id, 0, tex_format, tex_type, tex_init_data.size * tex_init_data.itemsize, pixels)
png.from_array(pixels.reshape(-1, tex_width * tex_channels), mode="RGBA").save("before1.png")

# Copy Texture data into a Pixel Buffer
pbo = glGenBuffers(1)
print(f"pbo {pbo}")
glBindBuffer(GL_PIXEL_PACK_BUFFER, pbo)
glBufferData(GL_PIXEL_PACK_BUFFER, tex_width * tex_height * tex_channels * np.dtype(np.uint8).itemsize, None, GL_STREAM_DRAW)
glBindTexture(GL_TEXTURE_2D, tex_id)
# glGetTexImage(GL_TEXTURE_2D, 0, tex_format, tex_type, 0)
glGetTextureImage(tex_id, 0, tex_format, tex_type, tex_init_data.size * tex_init_data.itemsize, ctypes.c_void_p(0))
glBindTexture(GL_TEXTURE_2D, 0)
glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)

err, gl_resource = cudart.cudaGraphicsGLRegisterBuffer(pbo, cudart.cudaGraphicsRegisterFlags.cudaGraphicsRegisterFlagsNone)
(err,) = cudart.cudaGraphicsMapResources(1, gl_resource, 0)
(err, dev_ptr, dev_buff_size) = cudart.cudaGraphicsResourceGetMappedPointer(gl_resource)
shape, strides, dtype = nbcuda.api.prepare_shape_strides_dtype(shape=(tex_width, tex_height, tex_channels), strides=None, dtype=np.uint8, order="C")
# datasize = nbcuda.driver.memory_size_from_info(shape, strides, dtype.itemsize)
mem_ptr = nbcuda.driver.MemoryPointer(context=nbcuda.current_context(), pointer=ctypes.c_uint64(dev_ptr), size=dev_buff_size)
dev_nd_array = nbcuda.cudadrv.devicearray.DeviceNDArray(shape, strides, dtype, gpu_data=mem_ptr)
# (err,) = cudart.cudaGraphicsUnmapResources(1, gl_resource, 0)

# threadsperblock = (16, 16, 4)
# blockspergrid_x = math.ceil(dev_nd_array.shape[0] / threadsperblock[0])
# blockspergrid_y = math.ceil(dev_nd_array.shape[1] / threadsperblock[1])
# blockspergrid_z = 4
# blockspergrid = (blockspergrid_x, blockspergrid_y, blockspergrid_z)
# process_pixels[blockspergrid, threadsperblock](dev_nd_array)

threadsperblock = (16, 16)
blockspergrid_x = math.ceil(dev_nd_array.shape[0] / threadsperblock[0])
blockspergrid_y = math.ceil(dev_nd_array.shape[1] / threadsperblock[1])
blockspergrid = (blockspergrid_x, blockspergrid_y)
process_pixels[blockspergrid, threadsperblock](dev_nd_array)

# # Process Pixel Buffer
# # TODO: REPLACE WITH CUDA PROCESSING
# glBindBuffer(GL_PIXEL_PACK_BUFFER, pbo)
# pixels_ptr = glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY)
# # processPixels(ptr, ...);
# map_array_ctype = (GLubyte * tex_width * tex_height * tex_channels).from_address(pixels_ptr)
# map_array = np.ctypeslib.as_array(map_array_ctype).reshape((512, 512, 4))
# map_array[:, :, 0] = 255 - map_array[:, :, 0]
# png.from_array(map_array.reshape(-1, tex_width * tex_channels), mode="RGBA").save("before2.png")
# glUnmapBuffer(GL_PIXEL_PACK_BUFFER)
# glBindBuffer(GL_PIXEL_PACK_BUFFER, 0)

# After Pixel Buffer is updated, copy Pixel buffer data into a Texture
glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo)
glBindTexture(GL_TEXTURE_2D, tex_id)
glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, tex_width, tex_height, tex_format, tex_type, ctypes.c_void_p(0))
glBindTexture(GL_TEXTURE_2D, 0)
glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)

pixels = np.empty(shape=(tex_width, tex_height, tex_channels), dtype=np.uint8)
glGetTextureImage(tex_id, 0, tex_format, tex_type, tex_init_data.size * tex_init_data.itemsize, pixels)
png.from_array(pixels.reshape(-1, tex_width * tex_channels), mode="RGBA").save("after.png")


# # No flag means read/write (for read-only: cudaGraphicsRegisterFlagsReadOnly, write-only: cudaGraphicsRegisterFlagsWriteDiscard) 
# err, gl_texture_resource = cudart.cudaGraphicsGLRegisterImage(tex_id, GL_TEXTURE_2D, GLFlags.cudaGraphicsRegisterFlagsNone)
# print(f"cudaGraphicsGLRegisterImage. error: {err}, res: {gl_texture_resource}")
# (err,) = cudart.cudaGraphicsMapResources(1, gl_texture_resource, 0)
# print(f"cudaGraphicsMapResources. error: {err}")
# # (err, dev_ptr, dev_ptr_size) = cudart.cudaGraphicsResourceGetMappedPointer(gl_texture_resource)
# # print(f"error: {err}, dev_ptr: {dev_ptr}, dev_ptr_size: {dev_ptr_size}")
# err, cuda_array = cudart.cudaGraphicsSubResourceGetMappedArray(gl_texture_resource, 0, 0)
# print(f"cudaGraphicsSubResourceGetMappedArray. error: {err}, array: {cuda_array}")
# err, channelformat, cudaextent, flag = cudart.cudaArrayGetInfo(cuda_array)
# print(f"cudaArrayGetInfo. error: {err}, channelformat: {channelformat}, cudaextent: {cudaextent}, flag: {flag}")
# # res = nbcuda.is_cuda_array(cuda_array)  # False
# # h_array = np.zeros(shape=(cudaextent.width, cudaextent.height, 4), dtype=np.uint8)
# # err, = cudart.cudaMemcpy2DArrayToArray(h_array.ctypes.data, 0, 0, cuda_array, 0, 0, cudaextent.width * 4 * 8, cudaextent.height, cudart.cudaMemcpyKind.cudaMemcpyDefault)  # cudaMemcpyDeviceToHost
# res_desc = cudart.cudaResourceDesc()
# res_desc.resType = cudart.cudaResourceType.cudaResourceTypeArray
# res_desc.res.array.array = cuda_array
# tex_desc = cudart.cudaTextureDesc()
# tex_desc.addressMode[0] = cudart.cudaTextureAddressMode.cudaAddressModeClamp
# tex_desc.addressMode[1] = cudart.cudaTextureAddressMode.cudaAddressModeClamp
# tex_desc.filterMode = cudart.cudaTextureFilterMode.cudaFilterModePoint  # default
# tex_desc.readMode = cudart.cudaTextureReadMode.cudaReadModeElementType  # default
# # res_view_desc = cudart.cudaResourceViewDesc()
# err, tex_obj = cudart.cudaCreateTextureObject(res_desc, tex_desc, None)
# res_view_desc = cudart.cudaGetTextureObjectResourceViewDesc(tex_obj)

while not glfw.window_should_close(window):
    glfw.poll_events()
    (w, h) = glfw.get_window_size(window)
    glViewport(0, 0, w, h)

    glClearColor(0.1, 0.2, 0.3, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) 

    glfw.swap_buffers(window)