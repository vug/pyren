#version 460

vec2 positions[3] = vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1, 3));
vec3 colors[3] = vec3[](vec3(1.0, 0.0, 0.0), vec3(0.0, 1.0, 0.0), vec3(0.0, 0.0, 1.0));

layout (location = 0) out vec3 fragColor;
// texcoords are in the normalized [0,1] range for the viewport-filling quad part of the triangle
layout (location = 1) out vec2 texCoords;

void main ()
{
	gl_Position = vec4 (positions[gl_VertexID], 0, 1);
	fragColor = colors[gl_VertexID];
	texCoords = 0.5 * gl_Position.xy + vec2(0.5);
}