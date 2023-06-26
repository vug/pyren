#version 460
uniform vec3 eyePos;

struct VertexData {
  vec3 objectPosition;
  vec3 worldPosition;
  vec3 objectNormal;
  vec3 worldNormal;
  vec2 texCoord;
  vec4 color;
  vec4 custom;
};

in VertexData v;

uniform int meshId;

layout (location = 0) out vec4 outColor;
layout (location = 1) out vec3 outWorldPos;
layout (location = 2) out vec3 outWorldNormal;
layout (location = 3) out vec2 outUV;
layout (location = 4) out int outMeshId;
layout (location = 5) out vec3 outMeshIdColored;

vec3 colorFromIndex(uint index) {
  uint a = (index & (1 << 0)) != 0 ? 1 : 0;
  uint d = (index & (1 << 1)) != 0 ? 1 : 0;
  uint g = (index & (1 << 2)) != 0 ? 1 : 0;

  uint b = (index & (1 << 3)) != 0 ? 1 : 0;
  uint e = (index & (1 << 4)) != 0 ? 1 : 0;
  uint h = (index & (1 << 5)) != 0 ? 1 : 0;

  uint c = (index & (1 << 6)) != 0 ? 1 : 0;
  uint f = (index & (1 << 7)) != 0 ? 1 : 0;
  uint i = (index & (1 << 8)) != 0 ? 1 : 0;

  return vec3(a*4+b*2+c, d*4+e*2+f, g*4+h*2+i) / 7.0f;
}

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
    outMeshId = meshId;
    outMeshIdColored = colorFromIndex(meshId);
}