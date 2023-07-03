#ifndef COMMON_GLSL
#define COMMON_GLSL

// A set of utility functions that can be included from anywhere thanks to "include guards"

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

float map(float value, float min1, float max1, float min2, float max2) {
  return min2 + (value - min1) * (max2 - min2) / (max1 - min1);
}

#endif