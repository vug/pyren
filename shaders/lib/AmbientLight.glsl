struct AmbientLight {
  vec3 color;
};

layout(location = 5) uniform AmbientLight ambientLight;

vec3 illuminate(AmbientLight light) {
  return light.color;
}