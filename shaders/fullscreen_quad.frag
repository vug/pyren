#version 460
layout (location = 0) in vec3 fragColor;
layout (location = 1) in vec2 texCoord;

#include "lib/scene_uniforms.glsl"
#include "lib/common.glsl"

#include "lib/AmbientLight.glsl"
#include "lib/DirectionalLight.glsl"
#include "lib/HemisphericalLight.glsl"
#include "lib/PointLight.glsl"

layout (binding = 0) uniform sampler2D sceneRenderTex;
layout (binding = 1) uniform sampler2D worldPosTex;
layout (binding = 2) uniform sampler2D worldNormalTex;
layout (binding = 3) uniform sampler2D uvTex;
layout (binding = 4) uniform isampler2D meshIdTex;

layout (location = 0) out vec4 outColor;

void main () { 
    int meshId = texture(meshIdTex, texCoord).r;
    // Discarding might not look good with MSAA
    if (meshId == 0)
        discard;

    const float specularCoef = 32.0;

    // retrieve data from G-buffer
    vec3 sceneRender = texture(sceneRenderTex, texCoord).rgb;
    vec3 worldPos = texture(worldPosTex, texCoord).rgb;
    vec3 worldNormal = texture(worldNormalTex, texCoord).rgb;
    vec2 uv = texture(uvTex, texCoord).rg;

       
    //outColor = vec4(fragColor, 1.0);
    //outColor = vec4(texCoord.x, texCoord.y, 0, 1);
    //outColor = vec4(worldPos, 1);    
    vec3 pointLight = vec3(0);
    for (int i = 0; i < numPointLights; i++)
      pointLight += illuminate(pointLights[i], worldPos, worldNormal, eyePos, specularCoef);
    vec3 color = vec3(
        illuminate(ambientLight)
        + illuminate(directionalLight, worldPos, worldNormal, eyePos, specularCoef)
        + illuminate(hemisphericalLight, worldNormal)
        + pointLight
    );
    outColor = vec4(color, 1.0);
}