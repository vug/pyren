#version 460 core
// #extension GL_GOOGLE_include_directive : enable
#extension GL_NV_fragment_shader_barycentric : require

#include "lib/vertex_data.glsl"
#include "lib/scene_uniforms.glsl"
#include "lib/common.glsl"

layout(location = 0) in VertexData v;

#include "lib/AmbientLight.glsl"
#include "lib/HemisphericalLight.glsl"

layout (location = 0) out vec4 outColor;
layout (location = 1) out vec3 outWorldPos;
layout (location = 2) out vec3 outWorldNormal;
layout (location = 3) out vec2 outUV;
layout (location = 4) out float outDepth;
layout (location = 5) out int outMeshId;
layout (location = 6) out vec3 outMeshIdColored;

float wireframe(vec3 vBC, float width) {
  vec3 bary = vec3(vBC.x, vBC.y, vBC.z);
  vec3 d = fwidth(bary);
  vec3 a3 = smoothstep(d * (width - 0.5), d * (width + 0.5), bary);
  return min(min(a3.x, a3.y), a3.z);
}

void main () {
    vec3 worldNormal = normalize(v.worldNormal);
    HemisphericalLight hemi = HemisphericalLight(vec3(1, 1, 1), vec3(0), 1.0);

    vec3 color = vec3(
        illuminate(hemi, worldNormal)
    );
    float wire = 1 - wireframe(gl_BaryCoordNV.xyz, 1.0);
    outColor = vec4(mix(color, vec3(0.2, 0.2, 0.2), wire), 1.0);

    // Data for deferred rendering
    outWorldPos = v.worldPosition;
    outWorldNormal = worldNormal;
    outUV = v.texCoord;
    outDepth = log(length(v.worldPosition - eyePos));  // TODO: add depthViz, and rename meshIdColored to meshIdViz
    outMeshId = meshId;
    outMeshIdColored = colorFromIndex(meshId);
}