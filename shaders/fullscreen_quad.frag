#version 460
layout (location = 0) in vec3 fragColor;
layout (location = 1) in vec2 texCoords;

layout (location = 0) uniform vec3 eyePos;

layout (binding = 0) uniform sampler2D sceneRenderTex;
layout (binding = 1) uniform sampler2D worldPosTex;
layout (binding = 2) uniform sampler2D worldNormalTex;
layout (binding = 3) uniform sampler2D uvTex;
layout (binding = 4) uniform isampler2D meshIdTex;

layout (location = 0) out vec4 outColor;

void main () { 
    int meshId = texture(meshIdTex, texCoords).r;
    // Discarding might not look good with MSAA
    if (meshId == 0)
        discard;

    // retrieve data from G-buffer
    vec3 sceneRender = texture(sceneRenderTex, texCoords).rgb;
    vec3 worldPos = texture(worldPosTex, texCoords).rgb;
    vec3 worldNormal = texture(worldNormalTex, texCoords).rgb;
    vec2 uv = texture(uvTex, texCoords).rg;
       
    vec3 lightPos = vec3(0.0f, 3.0f, 0.0f);
    vec3 surfToLight = lightPos - worldPos;
    float surfToLightMag = length(surfToLight);
    vec3 lightVec = surfToLight / surfToLightMag;
    float diffuse = max(dot(lightVec, worldNormal), 0) / (surfToLightMag * surfToLightMag);
    
    vec3 lightVecReflect = normalize(reflect(lightVec, worldNormal));
    vec3 surfToEye = eyePos - worldPos;
    vec3 eyeVec = normalize(surfToEye);
    float specular = max(pow(dot(lightVecReflect, eyeVec), 32), 0);

    //outColor = vec4(fragColor, 1.0);
    //outColor = vec4(texCoords.x, texCoords.y, 0, 1);
    //outColor = vec4(worldPos, 1);    
    outColor = vec4(vec3(diffuse + specular), 1.0);
}