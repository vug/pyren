#version 460
layout(location = 0) in vec3 objectPosition;
layout(location = 1) in vec2 texCoord;
layout(location = 2) in vec3 objectNormal;
layout(location = 3) in vec4 color;
vec4 custom = vec4(0);

uniform mat4 worldFromObject; // Model
uniform mat4 viewFromWorld; // View
uniform mat4 projectionFromView; // Projection

struct VertexData {
  vec3 objectPosition;
  vec3 worldPosition;
  vec3 objectNormal;
  vec3 worldNormal;
  vec2 texCoord;
  vec4 color;
  vec4 custom;
};

VertexData fillVertexData(mat4 worldFromObject, vec3 objectPosition, vec3 objectNormal, vec2 texCoord, vec4 color, vec4 custom) {
  VertexData v;
  v.objectPosition = objectPosition;
  v.worldPosition = vec3(worldFromObject * vec4(objectPosition, 1));
  v.objectNormal = objectNormal;
  v.worldNormal = mat3(transpose(inverse(worldFromObject))) * objectNormal;
  v.texCoord = texCoord;
  v.color = color;
  v.custom = custom;
  return v;
}    

out VertexData v;

void main () {
    v = fillVertexData(worldFromObject, objectPosition, objectNormal, texCoord, color, custom);
    gl_Position = projectionFromView * viewFromWorld * vec4(v.worldPosition, 1);
}