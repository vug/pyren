#version 460 core
// #extension GL_GOOGLE_include_directive : enable

#include "lib/vertex_data.glsl"
#include "lib/scene_uniforms.glsl"
#include "lib/common.glsl"

layout(location = 0) in VertexData v;

#include "lib/AmbientLight.glsl"

#include "lib/DirectionalLight.glsl"

#include "lib/HemisphericalLight.glsl"

#include "lib/PointLight.glsl"

layout (location = 0) out vec4 outColor;
layout (location = 1) out vec3 outWorldPos;
layout (location = 2) out vec3 outWorldNormal;
layout (location = 3) out vec2 outUV;
layout (location = 4) out float outDepth;
layout (location = 5) out int outMeshId;
layout (location = 6) out vec3 outMeshIdColored;

void main () {
    vec3 worldNormal = normalize(v.worldNormal);
    const float specularCoef = 32.0;

    vec3 pointLight = vec3(0);
    for (int i = 0; i < numPointLights; i++)
      pointLight += illuminate(pointLights[i], v.worldPosition, worldNormal, eyePos, specularCoef);
    const vec3 color = vec3(
        illuminate(ambientLight)
        + illuminate(directionalLight, v.worldPosition, worldNormal, eyePos, specularCoef)
        + illuminate(hemisphericalLight, worldNormal)
        + pointLight
    );
    outColor = vec4(color, 1.0);

    // Data for deferred rendering
    outWorldPos = v.worldPosition;
    outWorldNormal = worldNormal;
    outUV = v.texCoord;
    outDepth = log(length(v.worldPosition - eyePos));  // TODO: add depthViz, and rename meshIdColored to meshIdViz
    outMeshId = meshId;
    outMeshIdColored = colorFromIndex(meshId);
}