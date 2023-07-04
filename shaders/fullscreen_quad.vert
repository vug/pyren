#version 460

vec2 positions[3] = vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1, 3));
vec2 texCoords[3] = vec2[3](vec2( 0, 0), vec2(2, 0), vec2( 0, 2));

layout (location = 0) out vec3 fragColor;
// texcoords are in the normalized [0,1] range for the viewport-filling quad part of the triangle
layout (location = 1) out vec2 texCoord;

void main ()
{
	gl_Position = vec4(positions[gl_VertexID], 0, 1);
	texCoord = texCoords[gl_VertexID];
}