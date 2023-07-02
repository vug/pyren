layout(location = 0) uniform mat4 worldFromObject; // Model
layout(location = 1) uniform mat4 viewFromWorld; // View
layout(location = 2) uniform mat4 projectionFromView; // Projection
layout(location = 3) uniform vec3 eyePos;
layout(location = 4) uniform int meshId;