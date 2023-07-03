#version 460 core
// #extension GL_GOOGLE_include_directive : enable

#include "lib/vertex_data.glsl"
#include "lib/scene_uniforms.glsl"
#include "lib/common.glsl"

layout(location = 0) in vec3 objectPosition;
layout(location = 1) in vec2 texCoord;
layout(location = 2) in vec3 objectNormal;
layout(location = 3) in vec4 color;
vec4 custom = vec4(0);

layout(location = 0) out VertexData v;

void main () {
    v = fillVertexData(worldFromObject, objectPosition, objectNormal, texCoord, color, custom);
    gl_Position = projectionFromView * viewFromWorld * vec4(v.worldPosition, 1);
}