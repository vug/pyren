from mesh import Mesh
from shader import Shader
from texture import TextureDescription, Texture

import numpy as np
import pywavefront
from more_itertools import chunked, flatten

class Assets:
    def __init__(self, renderer):
        self.meshes: dict[str, Mesh] = {}
        self.shaders: dict[str, Shader] = {}
        self.textures: dict[str, Texture] = {}
        self._renderer = renderer
    
    def load_obj(self, asset_name: str, filename: str):
        obj_scene = pywavefront.Wavefront(filename, create_materials=True)
        
        for mesh_name in obj_scene.meshes:
            print(f"Mesh {mesh_name} found in {filename}")
        
        for name, mat in obj_scene.materials.items():
            print(f"name {name}, vertex format: {mat.vertex_format}, vertex size: {mat.vertex_size}, #verts {len(mat.vertices) / mat.vertex_size}")
            # process to work with pywavefront (no index buffers, specific vertex_format)
            vertices = chunked(mat.vertices, mat.vertex_size)  # each sub-list has a single flat vertex data
            ix = 0
            pos_ix, tex_ix, nrm_ix, col_ix = -1, -1, -1, -1
            if not mat.vertex_format:
                continue
            for attr in mat.vertex_format.split('_'):  # Ex: ["T2F", "N3F", "V3F"]
                n_comp = int(attr[1])
                if attr[0] == "V":  # Position
                    pos_ix = ix
                    assert(n_comp == 3)
                if attr[0] == "T":  # TexCoord
                    tex_ix = ix
                    assert(n_comp == 2)
                if attr[0] == "N":  # Normal
                    nrm_ix = ix
                    assert(n_comp == 3)
                if attr[0] == "C":  # Color
                    col_ix = ix
                    assert(n_comp == 3)
                ix += n_comp
            assert(pos_ix != -1)
            
            processed_vertices = []
            for v in vertices:
                pos = v[pos_ix : pos_ix + 3]
                tex = v[tex_ix : tex_ix + 2] if tex_ix != -1 else [0, 0]
                nrm = v[nrm_ix : nrm_ix + 3] if nrm_ix != -1 else [0, 0, 0]
                col = v[col_ix : col_ix + 3] + [1] if col_ix != -1 else [0, 0, 0, 1]
                w = list(flatten([pos, tex, nrm, col]))
                processed_vertices.append(w)
                
            processed_vertices = list(flatten(processed_vertices))
            np_array = np.array(processed_vertices, dtype=np.float32)
            mesh = Mesh(np_array)
            self.meshes[asset_name] = mesh
    
    def load_shader(self, asset_name: str, vert_file: str, frag_file: str):
        shader = Shader(vert_file, frag_file)
        self.shaders[asset_name] = shader
    
    def make_texture(self, asset_name: str, tex_desc: TextureDescription):
        texture = Texture(tex_desc)
        self.textures[asset_name] = texture