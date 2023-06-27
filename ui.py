from scene import Object

import imgui
import glm

class ComboBox:
    def __init__(self, label: str, seq, names, initial_ix=0):
        self.seq = seq
        self.names = names
        self.selected_ix = initial_ix
        self.label = label

    def draw(self):
        _, self.selected_ix = imgui.combo(self.label, self.selected_ix, self.names)
        selected_name = self.names[self.selected_ix]
        selected = self.seq[self.selected_ix]
        return self.selected_ix, selected_name, selected


def transform_widget(obj: Object):
    _, translation = imgui.slider_float3("translation", *obj.transform.translation, min_value=-10.0, max_value=10.0, format="%.3f")
    obj.transform.translation = glm.vec3(translation)
    _, rotation = imgui.slider_float3("rotation (YXZ)", *obj.transform.rotation_yxz, min_value=-10.0, max_value=10.0, format="%.3f")
    obj.transform.rotation_yxz = glm.vec3(rotation)
    _, scale = imgui.slider_float3("scale", *obj.transform.scale, min_value=0.0, max_value=10.0, format="%.3f")
    obj.transform.scale = glm.vec3(scale)        