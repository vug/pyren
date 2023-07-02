#version 460 core

#include "lib/common.glsl"

layout(location = 0) in VertexData v;
layout (location = 0) out vec4 outColor;
layout (location = 1) out vec3 outWorldPos;
layout (location = 2) out vec3 outWorldNormal;
layout (location = 3) out vec2 outUV;
layout (location = 4) out float outDepth;
layout (location = 5) out int outMeshId;
layout (location = 6) out vec3 outMeshIdColored;

void main () {
    vec3 lightPos = vec3(0.0f, 3.0f, 0.0f);
    vec3 surfToLight = lightPos - v.worldPosition;
    float surfToLightMag = length(surfToLight);
    vec3 lightVec = surfToLight / surfToLightMag;
    float diffuse = max(dot(lightVec, v.worldNormal), 0) / (surfToLightMag * surfToLightMag);
    
    vec3 lightVecReflect = normalize(reflect(lightVec, v.worldNormal));
    vec3 surfToEye = eyePos - v.worldPosition;
    vec3 eyeVec = normalize(surfToEye);
    float specular = max(pow(dot(lightVecReflect, eyeVec), 32), 0);

    outColor = vec4(vec3(diffuse + specular), 1.0);
    outWorldPos = v.worldPosition;
    outWorldNormal = v.worldNormal;
    outUV = v.texCoord;
    outDepth = log(length(v.worldPosition - eyePos));  // TODO: add depthViz, and rename meshIdColored to meshIdViz
    outMeshId = meshId;
    outMeshIdColored = colorFromIndex(meshId);
}