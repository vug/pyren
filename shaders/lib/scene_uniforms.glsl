layout(location = 0) uniform mat4 worldFromObject; // Model
layout(location = 1) uniform mat4 viewFromWorld; // View
layout(location = 2) uniform mat4 projectionFromView; // Projection
layout(location = 3) uniform vec3 eyePos;
layout(location = 4) uniform int meshId;
// layout(location = 5) uniform AmbientLight ambientLight; // declared in AmbientLight.glsl
// layout(location = 6) uniform DirectionalLight directionalLight; // declared in DirectionalLight.glsl
// layout(location = 9) uniform HemisphericalLight hemisphericalLight; // declared in HemisphericalLight.glsl
// layout(location = 12) uniform PointLight[MAX_POINT_LIGHTS] pointLights; // declared in PointLight.glsl
// layout(location = 36) uniform int numPointLights; // declared in PointLight.glsl