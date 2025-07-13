gaolianglizi_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

gaolianglizi_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform float time;
uniform ivec2 resolution;

out vec4 FragColor;

// 随机数生成器
float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 2D旋转函数
vec2 rotate(vec2 v, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat2(c, -s, s, c) * v;
}

void main() {
    float uTime = time + 0.033 * vTexId;

    ivec3 imgSize;

    int tex_id = vTexId;
    
    float uParticleDensity = 0.1;

    vec4 finalColor = vec4(0.0);
    vec2 uv = vTexCoord;
    
    // 采样源纹理并计算亮度 (NTSC公式)
    vec4 sourceColor = texture(renderedTexture, uv);
    float brightness = dot(sourceColor.rgb, vec3(0.299, 0.587, 0.114));
    
    // 基于亮度的粒子数量 (指数增长)
    float particleCount = ceil(pow(brightness, 0.5) * uParticleDensity * 20.0);
    
    // 火花粒子生成
    for(int i = 0; i < 30; i++) {
        if(float(i) >= particleCount) break;
        
        // 为每个粒子生成唯一种子
        vec2 seed = vec2(float(i), brightness * 100.0);
        
        // 随机参数
        float angle = rand(seed * 0.73) * 6.283;   // 初始角度
        float speed = rand(seed * 1.17) * 0.4 + 0.1; // 初速度
        float size = rand(seed * 2.39) * 0.01 + 0.002; // 粒子大小
        float life = rand(seed * 3.31) * 0.5 + 0.3;  // 生命周期
        
        // 时间偏移 (使粒子不同步)
        float t = uTime - rand(seed) * 2.0;
        
        // 粒子位置 (从源点发射)
        vec2 particlePos = uv;
        particlePos.y -= t * speed * 0.5;  // 基础下落
        
        // 应用重力加速度
        float gravity = 9.8;
        particlePos.y += 0.5 * gravity * t * t;
        
        // 随机运动 (旋转向量)
        vec2 randOffset = vec2(rand(seed * 5.0), rand(seed * 7.0));
        randOffset = rotate(randOffset, angle) * speed * 0.2;
        particlePos += randOffset * t;
        
        // 计算距离和大小
        vec2 diff = particlePos - uv;
        float dist = length(diff);
        
        // 粒子形状 (圆形)
        float particle = smoothstep(size, 0.0, dist);
        
        // 生命周期衰减 (抛物线衰减)
        float fade = 1.0 - smoothstep(0.0, life, t);
        fade *= fade;  // 二次衰减
        
        // 颜色渐变 (黄->橙->红)
        vec3 sparkColor = mix(
            vec3(1.0, 0.7, 0.2),    // 黄色
            mix(
                vec3(1.0, 0.4, 0.1), // 橙色
                vec3(0.8, 0.1, 0.0), // 红色
                smoothstep(0.0, 0.7, t/life)
            ),
            smoothstep(0.0, 0.3, t/life)
        );
        
        // 应用亮度和衰减
        sparkColor *= brightness * fade * particle;
        
        // 叠加到最终颜色
        finalColor.rgb += sparkColor;
    }
    
    // 添加辉光效果
    finalColor.rgb += finalColor.rgb * 1.5;
    finalColor.a = 1.0;
    
    FragColor = finalColor;

}
"""

jinfen_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

jinfen_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform float time;
uniform ivec2 resolution;

out vec4 FragColor;

// 随机数生成器
float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 2D噪声函数
float noise(vec2 p) {
    vec2 ip = floor(p);
    vec2 u = fract(p);
    u = u*u*(3.0-2.0*u);
    
    float res = mix(
        mix(rand(ip), rand(ip+vec2(1.0,0.0)), u.x),
        mix(rand(ip+vec2(0.0,1.0)), rand(ip+vec2(1.0,1.0)), u.x), u.y);
    return res*res;
}

void main() {
    float u_time = time + 0.033 * vTexId;

    ivec3 imgSize;

    int tex_id = vTexId;

    vec2 uv = vTexCoord;

    vec4 color = vec4(0);
    
    // 金粉参数
    int particleCount = 300;       // 粒子数量
    float particleSize = 0.003;    // 基本粒子大小
    float fallSpeed = 0.25;         // 基本下落速度
    float swayAmount = 0.4;        // 飘动幅度
    float sparkleIntensity = 8.0;  // 闪烁强度
    
    vec3 finalParticles = vec3(0.0);
    
    for (int i = 0; i < particleCount; i++) {
        // 为每个粒子创建唯一ID
        float id = float(i);
        
        // 粒子随机属性
        float seed = id * 100.0;
        float offset = rand(vec2(seed, seed)) * 100.0;
        float speed = fallSpeed * (0.5 + rand(vec2(seed, id)));
        float size = particleSize * (0.7 + 0.6 * rand(vec2(id, seed)));
        float swayFreq = 1.0 + 2.0 * rand(vec2(seed, id));
        float swayPhase = rand(vec2(id, seed)) * 10.0;
        
        // 粒子位置（循环下落）
        float yPos = fract(u_time * speed + offset);
        if(off_screen == 0){
            yPos = 1.0 - yPos;
        }
        
        vec2 particlePos = vec2(
            // X位置：随机起始点 + 正弦飘动
            rand(vec2(id, id)) + sin(u_time * swayFreq + swayPhase) * swayAmount * 0.1,
            // Y位置：从顶部落到底部后循环
            yPos
        );
        

        
        // 粒子到当前像素的距离
        vec2 dir = particlePos - uv;
        float dist = length(dir);
        
        // 绘制圆形粒子
        float particle = smoothstep(size, 0.0, dist);
        
        // 基础金色
        vec3 gold = vec3(1.0, 0.8, 0.3);
        
        // 磷光闪烁效果
        float sparkle = 0.0;
        float sparkleSeed = rand(vec2(id, u_time));
        if (sparkleSeed > 0.987) {
            // 闪烁持续时间
            float sparkleTime = fract(u_time * 5.0);
            // 闪烁强度曲线（快速出现，缓慢消失）
            sparkle = exp(-pow((sparkleTime - 0.1) * 10.0, 2.0));
            // 磷光颜色（蓝白）
            vec3 sparkleColor = mix(vec3(0.8, 0.9, 1.0), vec3(1.0), sparkle);
            gold = mix(gold, sparkleColor, 0.8) * sparkleIntensity;
        }
        
        // 应用距离衰减
        particle *= 1.0 - smoothstep(0.0, size * 2.0, dist);
        
        // 添加到总效果
        finalParticles += gold * particle;
    }
    
    // 混合到场景（加法混合）
    color.rgb += finalParticles * 0.4;


    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        uvec4 pixData = imageLoad(inputTex, writePos);

        pixData.rgb += uvec3(round(color.rgb * 255));
        imageStore(outputTex, writePos, pixData);
    } else{
        FragColor = texture(renderedTexture, vTexCoord);
        FragColor.rgb += color.rgb;
    }
}
"""

guangshu_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

guangshu_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform float time;
uniform ivec2 resolution;

out vec4 FragColor;

// 改进的随机数函数
float rand(vec2 n) { 
    return fract(sin(dot(n, vec2(12.9898, 78.233))) * 43758.5453);
}

// 改进的2D噪声函数 (更平滑)
float noise(vec2 p) {
    vec2 ip = floor(p);
    vec2 fp = fract(p);
    fp = fp * fp * (3.0 - 2.0 * fp); // 平滑曲线
    
    float a = rand(ip);
    float b = rand(ip + vec2(1.0, 0.0));
    float c = rand(ip + vec2(0.0, 1.0));
    float d = rand(ip + vec2(1.0, 1.0));
    
    return mix(mix(a, b, fp.x), mix(c, d, fp.x), fp.y);
}

// 改进的分形布朗运动 (更自然的流动)
float fbm(vec2 p) {
    float total = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    
    // 5次迭代创建平滑噪声
    for (int i = 0; i < 5; i++) {
        total += amplitude * noise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    return total;
}

// 改进的光线照射效果 (消除硬边界)
vec3 applyLightBeam(vec2 uv, vec3 color) {
    // 光束方向 (从左上角照射)
    vec2 lightDir = normalize(vec2(-0.8, -0.4));
    
    // 计算光束位置
    float beamPos = dot(uv, lightDir);
    
    // 更柔和的光束强度 (使用指数衰减)
    float beamIntensity = exp(-abs(beamPos - 0.15) * 4.0);
    
    // 光束颜色 (暖白色)
    vec3 beamColor = vec3(1.0, 0.96, 0.92) * beamIntensity;
    
    // 将光束应用到场景 (更柔和的混合)
    return color + beamColor * 0.3;
}

// 自然飘动的灰尘粒子
vec3 drawDust(vec2 uv, float time) {
    // 灰尘颜色 (暖白色)
    vec3 dustColor = vec3(1.0, 0.98, 0.95);
    
    // 最终颜色
    vec3 color = vec3(0.0);
    
    // 创建多个灰尘层
    for (int layer = 0; layer < 3; layer++) {
        float layerFactor = float(layer) * 0.3;
        
        // 灰尘位置 (使用时间相关的噪声)
        vec2 dustUV = uv * (0.8 + layerFactor * 0.2);
        dustUV += vec2(
            fbm(dustUV * 0.5 + time * 0.1 + layerFactor),
            fbm(dustUV * 0.5 + time * 0.15 + layerFactor + 10.0)
        ) * 0.2;
        
        // 灰尘密度 (使用FBM创建自然分布)
        float dustDensity = fbm(dustUV * 10.0 + time * 0.05);
        dustDensity = pow(dustDensity, 3.0);
        
        // 灰尘亮度 (在光束中增强)
        vec2 lightDir = normalize(vec2(-0.8, -0.4));
        float beamPos = dot(uv, lightDir);
        float brightness = exp(-abs(beamPos - 0.15) * 3.0) * 2.0;
        
        // 应用灰尘效果
        color += dustColor * dustDensity * brightness * (0.1 + layerFactor * 0.1);
    }
    
    return color;
}

// 体积光效果
vec3 applyVolumetricLight(vec2 uv, float time) {
    // 体积光方向 (与光束方向一致)
    vec2 lightDir = normalize(vec2(-0.8, -0.4));
    
    // 计算体积光位置
    float lightPos = dot(uv, lightDir);
    
    // 体积光强度 (使用指数衰减)
    float intensity = exp(-abs(lightPos - 0.15) * 3.0) * 0.5;
    
    // 创建体积光噪波 (随时间变化)
    vec2 noiseUV = uv * 3.0 + vec2(time * 0.1, 0.0);
    float noiseValue = fbm(noiseUV);
    
    // 体积光颜色
    vec3 lightColor = vec3(1.0, 0.95, 0.9) * intensity * noiseValue;
    
    return lightColor;
}


void main() {
    float f_time = time + 0.033 * vTexId;

    ivec3 imgSize;

    int tex_id = vTexId;

    vec2 uv = vTexCoord * 2 - 1;
    
    // 基础背景色 (深蓝灰色)
    vec3 color = vec3(0.0);
    
    // 添加环境光噪波
    float ambientNoise = fbm(uv * 5.0 + f_time * 0.05) * 0.02;
    color += vec3(ambientNoise);
    
    // 应用光束效果
    color = applyLightBeam(uv, color);
    
    // 添加体积光效果
    color += applyVolumetricLight(uv, f_time * 0.3);
    
    // 添加自然飘动的灰尘
    color += drawDust(uv, f_time * 0.8);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        uvec4 pixData = imageLoad(inputTex, writePos);
        
        pixData.rgb += uvec3(round(color * 255));
        imageStore(outputTex, writePos, pixData);
    } else{
        FragColor = texture(renderedTexture, vTexCoord);
        FragColor.rgb += color;
    }
}
"""

donggantuijing_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

donggantuijing_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform int fixed_img;
uniform float time;


out vec4 FragColor;

// 伪随机数生成器
float rand(vec2 co) {
  return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 2D噪声函数
float noise(vec2 p) {
  vec2 ip = floor(p);
  vec2 u = fract(p);
  u = u * u * (3.0 - 2.0 * u);

  float res = mix(
    mix(rand(ip), rand(ip + vec2(1.0, 0.0)), u.x),
    mix(rand(ip + vec2(0.0, 1.0)), rand(ip + vec2(1.0, 1.0)), u.x),
    u.y
  );
  return res * res;
}

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}

vec2 focusPoints[5] = vec2[](vec2(0.35, 0.3), vec2(0.7, 0.35), vec2(0.65, 0.65), vec2(0.45, 0.7), vec2(0.5, 0.5));

// 镜头移动和缩放函数
vec3 calculateFocusAndZoom(float time) {
    // 每个焦点停留时间
    float focusDuration = 0.3;

    int pointNum = 5;

    // 总周期时间
    float totalTime = pointNum * focusDuration;

    // 归一化时间（循环）
    float t = mod(time, totalTime);

    float divValue = t / focusDuration;

    int idx = int(floor(divValue));
    float fractionalPart = divValue - idx;

    fractionalPart = easeOutPow(fractionalPart, 5);

    // 停留在焦点1并放大
    int next_idx = int(mod(idx + 1, pointNum));
    vec2 currentFocus = mix(focusPoints[idx], focusPoints[next_idx], fractionalPart);

    vec2 disToCenter = abs(currentFocus - 0.5);

    // 缩放参数
    float zoomLevel = (0.5 - max(disToCenter.x, disToCenter.y)) * 2;

    return vec3(currentFocus, zoomLevel);
}

uniform float uSpeed=1.0;

void main() {
    float c_time = time + 0.033 * vTexId;
    
    ivec3 imgSize;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    // 计算当前焦点位置和缩放级别
    vec3 focusData = calculateFocusAndZoom(c_time * uSpeed);
    vec2 currentFocus = focusData.xy;
    float zoomLevel = focusData.z;

    // 应用缩放：以当前焦点为中心进行缩放
    uv = uv * zoomLevel;

    vec2 view_offset = currentFocus - zoomLevel * 0.5;
    uv += view_offset;

    // 计算当前像素到焦点的方向和距离（缩放后）
    vec2 dir = (uv - currentFocus)/zoomLevel;
    float dist = length(dir);

    // 添加动态噪声，使效果更自然
    float noiseFactor = noise(vec2(c_time * 0.5, dist * 10.0)) * 0.05;

    // 计算径向模糊强度（基于距离）
    float blur = 0.2 * pow(dist, 2.5) + noiseFactor;

    // 设置采样次数（性能与质量平衡）
    const int samples = 20;
    vec4 color = vec4(0.0);
    
    if(off_screen == 1){
        imgSize = imageSize(outputTex);
    }

    // 径向模糊采样
    for (int i = 0; i < samples; i++) {
        // 计算采样偏移（沿中心方向推进）
        float offset = float(i) / float(samples - 1);
    
        // 二次曲线偏移，使运动更自然
        float t = offset * offset;
    
        // 计算采样坐标（添加运动模糊）
        vec2 sampleCoord = uv + dir * blur * t;
    
        // 添加色散效果（RGB通道轻微偏移）
        vec2 dispDir = normalize(dir) * 0.007 * blur;
        
        vec3 disp;
        
        if(off_screen == 1){

            disp = vec3(
                imageLoad(inputTex, ivec3(imgSize.xy * (sampleCoord - dispDir), int(vTexId))).r / 255.0,
                imageLoad(inputTex, ivec3(imgSize.xy * (sampleCoord), int(vTexId))).g / 255.0,
                imageLoad(inputTex, ivec3(imgSize.xy * (sampleCoord + dispDir), int(vTexId))).b / 255.0
            );

        } else{
            disp = vec3(
                texture(renderedTexture, sampleCoord - dispDir).r,
                texture(renderedTexture, sampleCoord).g,
                texture(renderedTexture, sampleCoord + dispDir).b
            );
        }
    
        color += vec4(disp, 1.0);
    }

    color /= float(samples);

    
    // 增强焦点区域的对比度
    float focusMask = 1.0 - smoothstep(0.0, 0.6, dist);
    color.rgb = mix(color.rgb, color.rgb * 1.4, focusMask);
    
    // 添加边缘光晕效果
    float glow = smoothstep(0.6, 1.0, dist) * blur * 0.7;
    color.rgb += vec3(glow * 0.8, glow * 0.4, glow) * (0.5 + 0.5 * sin(c_time * 3.0));

    // 添加镜头暗角
    float vignette = 0.8 - smoothstep(0.3, 1.2, dist);
    color.rgb *= vignette * 0.8 + 0.2;

    
    FragColor = color;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    } 
}
"""

dingdaer_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

dingdaer_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform float time;
uniform ivec2 resolution;

out vec4 FragColor;

// 噪声函数 - 模拟大气扰动
float noise(vec2 p) {
    return fract(sin(dot(p.xy, vec2(12.9898,78.233))) * 43758.5453);
}

// 平滑噪声
float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    
    float a = noise(i);
    float b = noise(i + vec2(1.0, 0.0));
    float c = noise(i + vec2(0.0, 1.0));
    float d = noise(i + vec2(1.0, 1.0));
    
    vec2 u = f * f * (3.0 - 2.0 * f);
    
    return mix(a, b, u.x) + 
        (c - a) * u.y * (1.0 - u.x) + 
        (d - b) * u.x * u.y;
}

// 分形噪声
float fractalNoise(vec2 p) {
    float total = 0.0;
    float frequency = 1.0;
    float amplitude = 1.0;
    float maxValue = 0.0;
    
    for (int i = 0; i < 4; i++) {
        total += smoothNoise(p * frequency) * amplitude;
        maxValue += amplitude;
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    
    return total / maxValue;
}

void main() {
    float f_time = time + 0.033 * vTexId;
    
    ivec3 imgSize;
    
    int tex_id = vTexId;

    vec2 uv = vTexCoord;
    
    float u_speed = 6;
    float u_samples = 120;
    float u_noise = 0.05;
    float u_decay = 0.88;
    float u_density = 0.35;
    float u_intensity = 0.75;

    // 动态光源位置（随时间在右上角区域移动）
    float lightX = 0.9 + 0.3 * sin(f_time * 0.5 * u_speed);
    float lightY = 0.9 + 0.3 * cos(f_time * 0.3 * u_speed);
    if(off_screen == 1){
        imgSize = imageSize(outputTex);
        lightY = 0.1 + 0.3 * cos(f_time * 0.3 * u_speed);
    }
    vec2 lightPos = vec2(lightX, lightY);
    
    // 从当前像素指向光源的方向
    vec2 dir = lightPos - uv;
    float dist = length(dir);
    dir = normalize(dir);
    
    // 光线步进参数
    float numSamples = u_samples;
    if(dist > 0.6){
        numSamples *= 1.5;
    }
    float stepSize = dist / numSamples;
    
    // 添加随机偏移减少带状伪影
    vec2 jitter = vec2(noise(uv + f_time) - 0.5, noise(uv - f_time) - 0.5) * 0.002;
    
    // 初始化光线颜色和权重
    float light = 0;
    float weight = 1.0;
    float illuminationDecay = 1.0;
    
    vec2 noiseUV;
    
    // 光线步进循环
    for (int i = 0; i < u_samples; i++) {
        
        vec2 samplePos  = uv + dir * (float(i) * stepSize) + jitter;
        // 添加大气扰动
        float noiseValue = fractalNoise(samplePos  * 3.0 + f_time * 0.5 * u_speed);
        
        samplePos += u_noise * 0.02 * vec2(noiseValue, noise(samplePos + f_time));
        
        // 采样场景颜色
        vec3 sampleColor;
        
        if(off_screen == 1){
            sampleColor = imageLoad(inputTex, ivec3(samplePos * imgSize.xy, int(vTexId))).rgb / 255.0;
        } else{
            sampleColor = texture(renderedTexture, samplePos).rgb;
        }
        
        // 计算亮度
        float brightness = (sampleColor.r + sampleColor.g + sampleColor.b) / 3.0;
        
        // 应用指数衰减
        illuminationDecay *= u_decay;
        
        // 添加到光线效果（根据亮度和密度）
        light += brightness * illuminationDecay * u_density;
        
        // 权重递减（模拟光线在介质中的衰减）
        weight *= u_decay;
    }
    
    // 应用强度和颜色 - 随时间波动
    float timeIntensity = u_intensity * (0.6 + 0.1 * sin(f_time * u_speed * 0.7));
    light *= timeIntensity * 0.5;
    
    vec3 lightColor = vec3(1.0, 0.9, 0.7); // 暖色调光线
    vec3 rays = light * lightColor;
    
    // 添加辉光效果 - 随时间变化
    float glowIntensity = pow(light, 3.0) * (0.8 + 0.2 * sin(f_time * u_speed * 1.2));
    vec3 glowColor = glowIntensity * vec3(1.0, 0.8, 0.6) * 0.3;
    
    vec3 addColor = rays + glowColor;
    
    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        uvec4 pixData = imageLoad(inputTex, writePos);
        
        pixData.rgb += uvec3(round(addColor * 255));
        imageStore(outputTex, writePos, pixData);
    } else{
        FragColor = texture(renderedTexture, vTexCoord);
        FragColor.rgb += addColor;
    }
}
"""

yinghuochong_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;

    vTexId = gl_InstanceID;
}
"""

yinghuochong_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray inputTex;
layout(binding=1, rgba8ui) uniform uimage2DArray outputTex;

uniform sampler2D renderedTexture;

uniform int off_screen;
uniform float time;
uniform ivec2 resolution;

out vec4 FragColor;

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                       -0.577350269189626, 0.024390243902439);
    vec2 i  = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod(i, 289.0);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
        + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
        dot(x12.zw,x12.zw)), 0.0);
    m = m*m;
    m = m*m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
    vec3 g;
    g.x  = a0.x  * x0.x  + h.x  * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
}

void main() {
    float f_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    
    vec2 uv = vTexCoord * 2 - 1;
    
    // 荧光团参数
    const int COUNT = 10; // 增加数量
    float glow = 0.0;
    
    for(int i = 0; i < COUNT; i++) {
        // 每个荧光团的唯一ID
        float id = float(i);
        
        // 随时间变化的相位
        float t = f_time * (0.5 + 0.2 * sin(id * 0.7));
        
        // 位置动画 (使用多层噪声)
        vec2 pos = vec2(
            sin(id * 7.3) * 0.5 + snoise(vec2(t * 0.6, id * 4.2)) * 1.2,
            cos(id * 5.8) * 0.4 + snoise(vec2(id * 6.3, t * 0.7 + 17.3)) * 1.0
        );
        
        // 大小变化 (脉动效果)
        float size = 0.2 + 0.1 * sin(t * 0.8 + id * 3.0);
        
        size *= 0.002;
        
        // 计算距离
        float d = length(uv - pos);
        
        // 光晕计算 (使用大小参数)
        float intensity = size / (d * d + 0.0006); // 增强系数
        
        // 添加脉动效果
        intensity *= 3 * abs(sin(t * 2.2 + id * COUNT));
        
        // 添加到总光晕
        glow += intensity;
    }
    
    // 暖黄色调 (核心部分更黄，边缘偏橙)
    vec3 glowColor = mix(
        vec3(1.0, 0.8, 0.4),    // 亮黄色
        vec3(1.0, 0.5, 0.2),     // 橙红色
        smoothstep(0.0, 1.0, glow * 0.3)
    );
    
    // 混合到背景
    vec3 color = glow * glowColor;
    
    // 添加微弱的辉光效果
    color += pow(glow, 10.0) * vec3(1.0, 0.7, 0.3);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        uvec4 pixData = imageLoad(inputTex, writePos);
        pixData.rgb += ivec3(round(color * 255));
        imageStore(outputTex, writePos, pixData);
    } else{
        FragColor = texture(renderedTexture, vTexCoord);
        FragColor.rgb += color;
    }
}
"""

################################################################################################################


tupian_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;

    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

tupian_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    FragColor = texture(texture0, vec3(uv, tex_id));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

################################################################################################################
xiexian_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;

    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

xiexian_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}


void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    float progress = smoothstep(0, 1, c_time * 1.5);
    
    float diamond = max(uv.x * 0.5 + uv.y * 0.5, 0);

    // 分块显示
    float visible = step(diamond, progress);
    vec4 color = texture(texture0, vec3(uv, tex_id));
    
    // 添加边框效果
    float border = smoothstep(0.02, 0.0, abs(diamond - progress));
    vec3 borderColor = mix(color.rgb, vec3(1.0, 0.8, 0.2), border);

    FragColor = mix(vec4(0.0), vec4(borderColor, 1.0), visible);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

xuanwo_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;

    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

xuanwo_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}


void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    float progress = smoothstep(0, 1, c_time * 2);

    vec2 center = vec2(0.5);
    vec2 dir = uv - center;
    float dist = length(dir);
    
    // 动态扭曲强度 (随时间减少)
    float twist = mix(2.0, 0.0, progress) * (1.0 - dist);
    
    // 角度旋转
    float angle = twist * exp(-dist * 3.0);
    float cosA = cos(angle);
    float sinA = sin(angle);
    
    // 旋转矩阵
    mat2 rot = mat2(cosA, -sinA, sinA, cosA);
    vec2 twistedUV = center + rot * dir;
    
    // 边缘发光
    float glow = smoothstep(0.7, 0.0, dist) * (1.0 - progress);
    vec3 color = texture(texture0, vec3(twistedUV, tex_id)).rgb;
    color += vec3(0.0, 0.7, 1.0) * glow * 0.8;
    
    FragColor = vec4(color, 1.0);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""


saomiao_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;

    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

saomiao_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}


void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    float progress = smoothstep(0, 1, c_time * 2);

    //progress = easeOutPow(progress, 3);

    //float progress = abs(sin(c_time * 0.5));
    
    vec4 texColor = texture(texture0, vec3(uv, tex_id));

    // 扫描线效果
    float scanLine = sin(uv.y * 600.0 + progress * 5.0) * 0.1;
    
    // 色散效果
    float r = texture(texture0, vec3(uv + vec2(0.02 * (1.0 - progress)), tex_id), 0.0).r;
    float g = texture(texture0, vec3(uv + vec2(0.01 * (1.0 - progress)), tex_id), 0.0).g;
    float b = texture(texture0, vec3(uv, tex_id)).b;
    
    // 混合效果
    vec3 hologram = vec3(r, g, b) * (0.8 + scanLine);
    vec3 final = mix(texColor.rgb, hologram, 1.0 - progress);

    FragColor = vec4(final, 1.0);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""


xiangsufeiru_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

xiangsufeiru_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}


void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    float progress = smoothstep(0, 1, c_time * 2);
    
    progress = easeOutPow(progress, 3);
    
    //float progress = abs(sin(c_time * 0.5));

    vec2 grid = floor(uv * 1000.0);
    
    // 基于网格坐标的随机偏移
    float rand = fract(sin(dot(grid, vec2(12.9898, 78.233))) * 43758.5453);
    float delay = rand * 0.8; // 最大延迟0.8秒
    
    // 粒子动画进度
    float anim = progress;
    
    // 粒子起始位置 (屏幕外随机位置)
    vec2 startPos = vec2(rand, fract(rand * 3.0)) * 1.5 - 0.25;
    vec2 finalUV = mix(startPos, uv, anim);
    
    // 添加运动模糊
    vec2 blurVec = (finalUV - uv) * 0.1;
    vec4 color = texture(texture0, vec3(finalUV, tex_id));
    color += texture(texture0, vec3(finalUV - blurVec, tex_id));
    color += texture(texture0, vec3(finalUV - blurVec*2.0, tex_id));
    color /= 3.0;
    
    FragColor = color;
    
    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

yuanzhankai_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

yuanzhankai_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}


void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    vec2 uv = vTexCoord;

    float progress = smoothstep(0, 1, c_time * 2);
    
    progress = easeOutPow(progress, 3);

    vec2 center = vec2(0.5);
    float dist = distance(uv, center);
    float radius = progress * 0.8; // 半径扩大
    
    FragColor = texture(texture0, vec3(uv, tex_id));
    
    if (dist > radius) {
        FragColor *= 0;
    }

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

baiyechuang_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

baiyechuang_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    vec2 uv = vTexCoord;
    
    float progress = smoothstep(0, 1, c_time * 2);

    float blinds = 10.0; // 百叶窗数量
    float blindProgress = fract(uv.y * blinds) < progress ? 1.0 : 0.0;

    FragColor = texture(texture0, vec3(uv, tex_id)) * blindProgress;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

xuanru_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

xuanru_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}

void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    float progress = smoothstep(0, 1, c_time * 2);
    
    progress = easeOutPow(progress, 4);
    
    vec2 uv = vTexCoord;
    uv.xy -= 0.5;
    
    float angle = (1 - progress) * 3.14159;
    uv = mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * uv;
    uv += 0.5;

    FragColor = texture(texture0, vec3(uv, tex_id));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

huaru_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    
    vTexId = gl_InstanceID;
}
"""

huaru_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutPow(float t, float power) {
    return 1.0 - pow(1.0 - t, power);
}

void main() {
    float c_time = time + 0.033 * vTexId;

    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    float progress = smoothstep(0, 1, c_time * 1.5);
    progress = easeOutPow(progress, 5);
    
    vec2 uv = vTexCoord;
    
    uv.y += (1 - progress);
    
    vec4 totalColor = texture(texture0, vec3(uv, tex_id));
    
    /*
    vec4 totalColor = vec4(0.0);
    if(progress < 0.99){
        
        for (int i = 0; i < 5; i++) {
            float offset = float(i) * 0.04 * (1.0 - progress);
            vec2 coord = vec2(uv.x + offset, uv.y - offset);
            totalColor += texture(texture0, vec3(coord, tex_id));
        }
        totalColor /= 5;
    } else{
        totalColor = texture(texture0, vec3(uv, tex_id));
    }
    */
    
    FragColor = totalColor;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

danru_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

danru_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float easeOutExpo(float t) {
    return sin((t * 3.14159) / 2.0);
}

void main() {
    float c_time = time + 0.033 * vTexId;
    
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    float progress = smoothstep(0, 1, c_time * 2);
    
    progress = easeOutExpo(progress);
    
    FragColor = texture(texture0, vec3(vTexCoord, tex_id));
    
    FragColor.rgba *= progress;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""
################################################################################################################


################################################################################################################
jinggao_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);
    vTexId = gl_InstanceID;
    
    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

jinggao_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;


out vec4 FragColor;


void main() {
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    float f_time = time + vTexId * 0.033;
    
    float u_intensity = 0.3 * abs(sin(f_time * 3));
    
    float disToCenter = length(vTexCoord - (0.5, 0.5));
    float distance = disToCenter * 2.0;
    
    float redFactor = pow(distance, 2) * u_intensity;

    FragColor = texture(texture0, vec3(vTexCoord, tex_id));
    
    vec3 warningColor = vec3(1.0, 0.0, 0.0); // 纯红色
    FragColor.rgb = mix(FragColor.rgb, warningColor, redFactor);
    FragColor.r += redFactor * 0.5;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

doudong_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);
    vTexId = gl_InstanceID;
    
    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

doudong_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

float u_intensity = 0.2;

// 伪随机数生成
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

void main() {
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    float f_time = time + vTexId * 0.033;
    f_time *= 0.1;
    
    vec2 shake = vec2(random(vec2(f_time)) - 0.5, random(vec2(f_time + 1.0)) - 0.5) * u_intensity * 0.1;

    FragColor = texture(texture0, vec3(vTexCoord + shake, tex_id));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

yidong_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;
uniform float time;


uniform float cut_v;

float mapVariable(float input) {
    // 将输入变量映射到一个周期为12的循环
    float cycle = mod(input, 20.0);

    // 如果在0到5之间，直接返回；如果在3到6之间，返回6 - cycle
    return cycle < 10.0 ? cycle : 20.0 - cycle;
}

void main() {
    gl_Position = vec4(aPosition, 1.0);
    vTexId = gl_InstanceID;
    
    float f_time = time + vTexId * 0.033;
    f_time = mapVariable(f_time);
    
    float progress = smoothstep(0.0, 1.0, f_time/10);
    
    vTexCoord = aTexCoord;
    vec2 move_dir = vec2(0.0, 0.2);
    vTexCoord.y *= 0.75;
    
    /*
    if(cut_v > 1.5){
        move_dir = vec2(0.0, 0.1375);
    } else{
        move_dir = vec2(0.0, -0.2);
    }
    */
    
    if(off_screen == 0){
        vTexCoord.y = 0.75 - vTexCoord.y;
    }
    
    vTexCoord += progress * move_dir;

}
"""

yidong_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoise(vec2 v) {
    const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                       -0.577350269189626, 0.024390243902439);
    vec2 i  = floor(v + dot(v, C.yy));
    vec2 x0 = v - i + dot(i, C.xx);
    vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
    vec4 x12 = x0.xyxy + C.xxzz;
    x12.xy -= i1;
    i = mod(i, 289.0);
    vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
        + i.x + vec3(0.0, i1.x, 1.0));
    vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
        dot(x12.zw,x12.zw)), 0.0);
    m = m*m;
    m = m*m;
    vec3 x = 2.0 * fract(p * C.www) - 1.0;
    vec3 h = abs(x) - 0.5;
    vec3 ox = floor(x + 0.5);
    vec3 a0 = x - ox;
    m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
    vec3 g;
    g.x  = a0.x  * x0.x  + h.x  * x0.y;
    g.yz = a0.yz * x12.xz + h.yz * x12.yw;
    return 130.0 * dot(m, g);
}

void main() {
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    vec2 uv;
    
    if(off_screen == 1){
        uv = gl_FragCoord.xy / vec2(1024, 768) * 2 - 1;
    } else {
        uv = gl_FragCoord.xy / vec2(512, 384) * 2 - 1;
    }
    
    float f_time = time + vTexId * 0.033;

    vec3 color = texture(texture0, vec3(vTexCoord, tex_id)).xyz;
    
    /*
    // 荧光团参数
    const int COUNT = 6; // 增加数量
    float glow = 0.0;
    
    for(int i = 0; i < COUNT; i++) {
        // 每个荧光团的唯一ID
        float id = float(i);
        
        // 随时间变化的相位
        float t = f_time * (0.5 + 0.2 * sin(id * 0.7));
        
        t *= 0.15;
        
        // 位置动画 (使用多层噪声)
        vec2 pos = vec2(
            sin(id * 7.3) * 0.5 + snoise(vec2(t * 0.7, id * 4.2)) * 1.2,
            cos(id * 5.8) * 0.4 + snoise(vec2(id * 6.3, t * 0.9 + 17.3)) * 1.0
        );
        
        // 大小变化 (脉动效果)
        float size = 0.6 + 0.4 * sin(t * 0.8 + id * 3.0);
        
        size *= 0.006;
        
        // 计算距离
        float d = length(uv - pos);
        
        // 光晕计算 (使用大小参数)
        float intensity = size / (d * d + 0.01); // 增强系数
        
        // 添加脉动效果
        intensity *= 1 + 0.6 * sin(t * 1.2 + id * 8.0);
        
        // 添加到总光晕
        glow += intensity;
    }
    
    // 暖黄色调 (核心部分更黄，边缘偏橙)
    vec3 glowColor = mix(
        vec3(1.0, 0.8, 0.4),    // 亮黄色
        vec3(1.0, 0.5, 0.2),     // 橙红色
        smoothstep(0.0, 1.0, glow * 0.3)
    );
    
    // 混合到背景
    color += glow * glowColor;
    
    // 添加微弱的辉光效果
    color += pow(glow, 4.0) * vec3(1.0, 0.7, 0.3) * 0.3;
    
    
    */
    
    FragColor = vec4(color,1.0);

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

fanye_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
out float back;
flat out int vTexId;

uniform float time;
uniform int off_screen;

vec3 rotatePoint(vec3 p, vec3 axis, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return p * c + cross(axis, p) * s + axis * dot(axis, p) * (1.0 - c);
}

mat4 rotateAroundAxis(vec3 axis, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    float omc = 1.0 - c;
    
    return mat4(
        c + axis.x * axis.x * omc,        // 第一列
        axis.x * axis.y * omc - axis.z * s,
        axis.x * axis.z * omc + axis.y * s,
        0,

        axis.y * axis.x * omc + axis.z * s, // 第二列
        c + axis.y * axis.y * omc,
        axis.y * axis.z * omc - axis.x * s,
        0,

        axis.z * axis.x * omc - axis.y * s, // 第三列
        axis.z * axis.y * omc + axis.x * s,
        c + axis.z * axis.z * omc,
        0,

        0, 0, 0, 1                        // 第四列
    );
}

void main() {
    vTexCoord = aTexCoord;
    vTexCoord.y *= 0.75;
    
    if(off_screen == 0){
        vTexCoord.y += 0.25;
        vTexCoord.y = 1 - vTexCoord.y;
    }
    
    vTexId = gl_InstanceID;

    float f_time = time + vTexId * 0.033;
    float uProgress = 1 - smoothstep(0.0, 1.0, f_time * 1);
    
    vec2 uFoldOrigin = vec2(1.0, -1.0);
    vec2 pos = aPosition.xy;
    vec2 dir = pos - uFoldOrigin;
    float dist = length(dir) * 0.5;
    back = uProgress - dist;
    
    if(dist <= uProgress) {
        vec3 axis = normalize(vec3(1.0, 1.0, 0.0));
        float angle = 3.14 * uProgress * (1 - smoothstep(0.0, uProgress, dist));
        
        vec3 oriPos = axis * dist;
        
        vec4 newPos = vec4(aPosition - oriPos, 1);
        
        mat4 rotM = rotateAroundAxis(axis, angle);
        
        //gl_Position = vec4(rotatePoint(aPosition.xyz, axis, angle), 1.0);
        
        newPos = rotM * newPos;
        
        newPos.xyz += oriPos;
        
        gl_Position = newPos;
    } else{
        gl_Position = vec4(aPosition, 1.0);
    }
}
"""

fanye_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
in float back;
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;
uniform float time;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

void main() {
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }
    
    if(back > 0) {
        FragColor = texture(texture0, vec3(vTexCoord, tex_id)) * back;
    } else{
        FragColor = texture(texture0, vec3(vTexCoord, tex_id));
    }

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""
################################################################################################################

suiping_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;
layout(location = 3) in vec3 aNormal;

out vec2 vTexCoord;
out vec3 vColor;
uniform float time;
uniform mat4 projectionMatrix;
uniform int off_screen;

out vec3 FragPos; // 传递到片段着色器的片段位置
out vec3 Normal; // 传递到片段着色器的法线
flat out int vTexId;

float rand(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// 函数：计算旋转矩阵
mat4 rotationMatrix(float angle) {
    // 初始化随机数生成器的状态

    vec3 axis = normalize(vec3(rand(vec2(aRotPos.x, aRotPos.y)) * 2 - 1, rand(vec2(aRotPos.x, 1 - aRotPos.y)) * 2 - 1, rand(vec2(1- aRotPos.x, 1 - aRotPos.y)) * 2 - 1));

    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;

    return mat4(
        oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
        oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
        oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,          0.0,
        0.0,                                0.0,                                0.0,                                1.0
    );
}

float mapVariable(float input) {
    // 将输入变量映射到一个周期为6的循环
    float cycle = mod(input, 6.0);

    // 如果在0到5之间，直接返回；如果在3到6之间，返回6 - cycle
    return cycle < 3.0 ? cycle : 6.0 - cycle;
}

void main() {
    // 平移到旋转中心点
    vec3 translatedVertex = aPosition - aRotPos;

    // 初始化随机数生成器的状态
    float rand_num = rand(aRotPos.xy);


    // 生成随机
    float c_time = time + 0.033 * gl_InstanceID;

    c_time = mapVariable(c_time);

    float rot_value = (rand_num * 2) * pow(c_time,2);

    float move_value = (2 - rand_num * 2) * pow(c_time,2);


    if(c_time > 0){
        // 应用旋转矩阵
        mat4 rotMatrix = rotationMatrix(rot_value);
        vec3 rotatedVertex = (rotMatrix * vec4(translatedVertex, 1.0)).xyz;

        mat3 normalMat = transpose(inverse(mat3(rotMatrix)));

        vec3 offset = aRotPos;
        offset = move_value * aRotPos;

        Normal = normalMat * aNormal;

        gl_Position = projectionMatrix * vec4(rotatedVertex + aRotPos + offset, 1.0);
        //gl_Position = vec4(rotatedVertex + aRotPos + offset, 1.0);
    } else {
        gl_Position = projectionMatrix * vec4(aPosition, 1.0);
        //gl_Position = vec4(aPosition, 1.0);
        Normal = aNormal;
    }

    if(Normal.z > 0){
        Normal *= -1;
    }

    //gl_Position.z *= -1;
    //gl_Position.z -= 0.5;
    FragPos = gl_Position.xyz;
    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }

    vTexId = gl_InstanceID;
}
"""

suiping_fragment = """
#version 430 core
in vec3 vColor;
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
in vec3 FragPos; // 从顶点着色器传递的片段位置
in vec3 Normal; // 从顶点着色器传递的法线
flat in int vTexId;

vec3 lightPos = vec3(0.2, 1, -1); // 光源位置
vec3 viewPos = vec3(0, 0, -1); // 观察者位置
vec3 lightColor = vec3(1, 1, 1); // 光源颜色

// 纹理数组 
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform float time;
uniform int off_screen;

out vec4 FragColor;

// 镜面反射计算（Blinn-Phong模型）
vec3 calculateSpecular(vec3 normal, vec3 lightDir, vec3 viewDir) {
    vec3 halfVec = normalize(lightDir + viewDir); // 半角向量
    float spec = pow(max(dot(normal, halfVec) * 1.2, 0.0), 32); // 镜面反射强度
    return spec * lightColor; // 镜面反射光
}

void main() {
    float f_time = time + 0.033 * vTexId;

    // 流光效果的动态噪声
    //vec2 uv = vTexCoord * 0.1 + vec2(time * 0.8, time * 0.3); // 缩放和时间偏移

    // 流光动态变化
    //float flow = smoothstep(0.1, 0.5, sin(uv.x * 5.0 + uv.y * 5.0 + time * 2.0));

    // 镜面反射计算
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 specular = calculateSpecular(norm, lightDir, viewDir);

    vec3 light_color = specular * 0.01;


    FragColor = texture(texture0, vec3(vTexCoord, vTexId));
    FragColor.rgb += light_color;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        //uint saveCol = imageLoad(outputTex, writePos).z;

        imageStore(outputTex, writePos, uvec4((FragColor).rgb * 255, 0));
    } 
}
"""

wutaidengguang_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

wutaidengguang_fragment = """
#version 430 core
in vec2 vTexCoord;
flat in int vTexId;

layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

uniform float time;

#define PI 3.14159265359

// 噪声函数（用于雾效）
float noise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453);
}

// 在原有代码基础上添加
vec3 depthFog(vec2 uv, vec3 fogColor, float density) {
    float depth = length(uv - vec2(0.5)); // 到画面中心的距离
    float fogFactor = exp(-depth * density); // 指数衰减
    return mix(fogColor, vec3(0.0), fogFactor);
}

// 新版聚光灯函数（固定起点，动态方向）
float dynamicSpotlight(vec2 uv, vec2 origin, float angle, float coneAngle) {
    // 向量计算
    vec2 dirVec = vec2(sin(angle), -cos(angle)); // 方向向量
    vec2 toFrag = uv - origin;
    float distanceFactor = 1 - smoothstep(0.0, 1.0, length(toFrag)); // 距离衰减

    // 锥形角度计算
    float dirDot = dot(normalize(toFrag), dirVec);
    float cone = smoothstep(cos(coneAngle*0.5), 1.0, dirDot);

    // 组合效果
    return cone * distanceFactor;
}

vec3 motionFog(vec2 uv, float time) {
    vec3 fog = vec3(0.0);
    for(int i=0; i<3; i++){
        float t = time - float(i)*0.2; // 相位偏移
        vec2 pos = vec2(sin(t)*0.5+0.5, cos(t*0.7)*0.3+0.4);
        fog += 0.3/length(uv - pos);
    }
    return fog * vec3(0.3,0.5,0.8);
}

void main() {
    vec2 uv = vTexCoord;
    uv.y = 1 - uv.y;

    float u_time = time + vTexId * 0.033;

    // 动态方向参数
    float swingSpeed = 4.2;
    float swingRange = PI * 0.15; // 摆动范围

    float originX[4] = float[](0.2, 0.4, 0.6, 0.8);
    vec3 spotColors[10];
    spotColors[0] = vec3(0.8,0.9,1.0);
    spotColors[1] = vec3(0.4,0.6,1.0);
    spotColors[2] =  vec3(0.8, 0.2, 1.0);  // 品红
    spotColors[3] = vec3(0.3, 0.9, 1.0);  // 青蓝
    spotColors[4] = vec3(0.4, 0.9, 0.3);  // 翠绿
    spotColors[5] = vec3(0.2, 0.6, 0.4);  // 深绿
    spotColors[6] = vec3(0.7, 0.3, 1.0);  // 薰衣草紫
    spotColors[7] = vec3(1.0, 0.8, 0.2);  // 鎏金色
    spotColors[8] = vec3(1.0, 0.6, 0.2);  // 琥珀色
    spotColors[9] = vec3(1.0, 0.3, 0.1);  // 橙红

    float timeIndex = floor(u_time); // 每2秒切换一次

    vec3 spotLight = vec3(0, 0, 0);

    int idx;
    for(int i=0; i<4; i++){
        float offset = sin(timeIndex) * 0.1 * PI;
        vec2 lightOrigin = vec2(originX[i], 1.05);
        float currentAngle = sin(u_time * swingSpeed + i * PI * 0.2) * swingRange;

        float stren = 0;

        for(int j=0; j<3; j++){
            float historyAngle = currentAngle - float(j)*0.1;
            stren += dynamicSpotlight(uv, lightOrigin, historyAngle, PI*0.1 + offset) * 0.4;
        }

        idx = int(mod(timeIndex + i, 5.0)) * 2;
        spotLight+= mix(spotColors[idx], spotColors[idx + 1], stren) * stren;

        // 添加光柱辉光
        float beamCore = smoothstep(0.4, 1.0, stren);
        spotLight += spotColors[idx] * beamCore;
    }

    vec3 final = spotLight;

    // 使用示例  
    vec3 fog = depthFog(uv, spotColors[int(mod(timeIndex, 5.0))] * 0.5, 2.5);

    // 合成最终效果
    final += fog;

    FragColor = texture(texture0, vec3(vTexCoord, vTexId));
    FragColor.xyz += final;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor * 255));
    }
}
"""

heidong_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

heidong_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

uniform float time;

const float blackHoleRadius = 0.4; // 黑洞半径

float DeflectionAngle(vec2 pos){
    return 90/length(pos);
}

// Rodrigues' Rotation Formula
vec3 rotateAroundAxis(vec3 v, vec3 k, float angle) {
    // 确保 k 是单位向量
    k = normalize(k);

    // 计算旋转后的向量
    float cosTheta = cos(angle);
    float sinTheta = sin(angle);
    vec3 kv = cross(k, v);
    vec3 result = v * cosTheta + kv * sinTheta + k * dot(k, v) * (1.0 - cosTheta);

    return result;
}

void main() {
    float f_time = time + vTexId * 0.033;

    vec2 shake = vec2(sin(f_time * 0.6) * 0.04, cos(f_time * 0.5) * 0.03);
    vec2 center = vec2(0, 0) + shake;
    vec2 pos = vTexCoord * 2 - 1;

    float angel = DeflectionAngle(pos);

    float len = length(pos - center); 
    if(len > blackHoleRadius){
        vec3 originalVector = vec3(0.0, 0.0, -1.0); // 原始向量

        vec3 rotationAxis = normalize(vec3(pos - center, 0.0));  // 旋转轴（例如 Z 轴）
        float angle = radians(angel);          
        vec3 rotatedVector = rotateAroundAxis(originalVector, rotationAxis, angle);

        vec2 newUV = pos + rotatedVector.xy * 0.5 * (1.2 - (len - blackHoleRadius));
        newUV = (newUV + 1) * 0.5;
        newUV.x = smoothstep(-0.3, 1.3, newUV.x);
        newUV.y = smoothstep(-0.3, 1.3, newUV.y);
        FragColor = texture(texture0, vec3(newUV, vTexId)); 
    }
    else{
        /*
        vec3 dir = vec3(pos.x, pos.y, 0.16 - pos.x*pos.x - pos.y*pos.y);
        float spec = max(dot(dir, vec3(0, 0, 1)), 0.0);
        FragColor = texture(texture0, vTexCoord) * spec;*/
        FragColor = vec4(0, 0, 0, 0);
    } 

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
}
"""

crtpingmu_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;


out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

crtpingmu_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

uniform float time;

void main() {
    vec2 uv = vTexCoord;

    float f_time = time + vTexId * 0.033;

    // 扫描线
    float scanLine = sin(uv.y * 1080 + f_time * 1000.0) * 0.1;

    // RGB 通道偏移（色差）
    float r = texture(texture0, vec3(uv + vec2(0.01, 0.0), vTexId)).r;
    float g = texture(texture0, vec3(uv + vec2(0.0, 0.005), vTexId)).g;
    float b = texture(texture0, vec3(uv - vec2(0.01, 0.0), vTexId)).b;

    // 暗角效果
    vec2 vignette = uv * (1.0 - uv);
    float vig = vignette.x * vignette.y * 15.0;

    FragColor = vec4(r + scanLine, g + scanLine, b + scanLine, 1.0) * vig;


    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
} 
"""

zaoyin_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;


out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

zaoyin_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

uniform float time;

float noise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}
// 模拟水面波纹 + 动态噪声
void main() {
    vec2 uv = vTexCoord;
    float f_time = time + vTexId * 0.033;

    // 动态波纹
    float wave = sin(uv.x * 20.0 + f_time * 5.0) * 0.02;
    wave += sin(uv.y * 15.0 + f_time * 3.0) * 0.03;

    // 添加噪声
    uv += wave + noise(uv * 10.0 + f_time) * 0.03;

    // 颜色混合
    vec3 col = mix(vec3(0.1, 0.3, 0.5), vec3(0.8, 0.9, 1.0), uv.y + wave) * 0.5;

    FragColor = texture(texture0, vec3(uv,vTexId));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
} 
"""

niuqu_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

niuqu_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

uniform float time;

void main() {

    float f_time = time + vTexId * 0.033;

    vec2 uv = vTexCoord;
    vec2 offset = vec2(sin(uv.y * 10.0 + f_time * 20), cos(uv.x * 10.0 + f_time * 20)) * 0.02;

    FragColor = texture(texture0, vec3(uv + offset, vTexId));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
} 
"""

baoguang_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
uniform int off_screen;

flat out int vTexId;

void main() {

    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

baoguang_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;

out vec4 FragColor;

void main() {

    vec4 center = texture(texture0, vec3(vTexCoord, vTexId));

    vec4 left = texture(texture0, vec3(vTexCoord+ vec2(-0.01, 0.0), vTexId)); 

    vec4 right = texture(texture0, vec3(vTexCoord + vec2(0.01, 0.0), vTexId));

    vec4 top = texture(texture0, vec3(vTexCoord + vec2(0.0, 0.01), vTexId));

    vec4 bottom = texture(texture0, vec3(vTexCoord + vec2(0.0, -0.01), vTexId));

    vec4 edge = center * 4.0 - (left + right + top + bottom);
    FragColor = center + edge * 0.5;

    vec4 glow = vec4(1.0);
    float intensity = 0.0;
    for (float i = 0.0; i < 10.0; i++) {
        vec2 offset = vec2(sin(i * 0.1), cos(i * 0.1)) * 0.01 * i;
        glow += texture(texture0, vec3(vTexCoord + offset, vTexId)) * (1.0 - i * 0.1); 
        intensity += 1.0 - i * 0.1;
    }
    glow /= intensity;

    FragColor = center + glow;
    FragColor *= 0.6;

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
} 
"""

face_replace_vertex = """
#version 430 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aFaceCoord;

out vec2 vTexCoord;
out vec2 vFaceCoord;

flat out lowp int vOutFace;
flat out int vTexId;

uniform int off_screen;

void main() {
    vTexCoord = aPosition.xy;

    vec2 pos = aPosition.xy;
    pos = pos * 2 - 1;
    gl_Position = vec4(pos, 0, 1.0);

    vFaceCoord = aFaceCoord;
    if(vFaceCoord.x == 0 && vFaceCoord.y==0){
        vOutFace = 1;
    }

    if(off_screen == 0){
        gl_Position.y *= -1;
    }

    vTexId = int(aPosition.z);
}
"""

face_replace_fragment = """
#version 430 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
in vec2 vFaceCoord;

flat in lowp int vOutFace;
flat in int vTexId;


// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform sampler2D face; // 纹理采样器

uniform int off_screen;

out vec4 FragColor;

void main() {
    if(vOutFace == 1){
        //ivec3 readPos = ivec3(vTexCoord * textureSize(texture0, 0).xy, int(vTexId));
        //FragColor = vec4(texelFetch(texture0, readPos, 0).rgb, 1);
        FragColor = texture(texture0, vec3(vTexCoord, vTexId));
    } else{
        FragColor = texture(face, vFaceCoord);
    }

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        imageStore(outputTex, writePos, ivec4(FragColor*255));
    }
}
"""



wuxiaoguo_vertex = """
#version 420 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;
flat out int vTexId;

uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
    vTexId = gl_InstanceID;
}
"""

wuxiaoguo_fragment = """
#version 420 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
flat in int vTexId;

// 纹理数组
layout(binding=0, rgba8ui) uniform uimage2DArray outputTex;
uniform sampler2DArray texture0;

uniform int off_screen;
uniform int fixed_img;

// 单纹理
//uniform sampler2D texture0;

out vec4 FragColor;

void main() {
    int tex_id = vTexId;
    if(fixed_img == 1){
        tex_id = 0;
    }

    FragColor = texture(texture0, vec3(vTexCoord, tex_id));

    if(off_screen == 1){
        ivec3 writePos = ivec3(gl_FragCoord.xy, int(vTexId));
        ivec4 outputColor = ivec4(round(FragColor * 255.0));
        imageStore(outputTex, writePos, outputColor);
    }
}
"""

xuanzhuan_niuqu_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;

uniform float time;
uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);
    
    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

xuanzhuan_niuqu_fragment = """
#version 330 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
uniform float time;

uniform sampler2D texture0; // 纹理采样器

out vec4 FragColor;

mat2 rotationMatrix(float angle) {
    return mat2(
        cos(angle), -sin(angle),
        sin(angle), cos(angle)     
    );
}

void main() {
    vec2 uv = vTexCoord * 2 - 1;

    float distort = length(uv) * 4 - time * 0.2; // 扭曲程度

    vec2 newUV = rotationMatrix(distort) * uv;
    newUV = (newUV + 1) * 0.5;
    FragColor = texture(texture0, newUV);
    FragColor.xz = FragColor.zx;
}
"""





liuguang_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;

out vec2 vTexCoord; // 传递到片段着色器的纹理坐标
out vec3 FragPos; // 传递到片段着色器的片段位置
out vec3 Normal; // 传递到片段着色器的法线

void main() {
    // 计算片段的世界空间位置
    FragPos = aPosition;

    // 计算法线的变换（注意：需要使用模型矩阵的逆矩阵的转置来变换法线）
    Normal = vec3(0, 0, -1);

    // 传递纹理坐标
    vTexCoord = aTexCoord;

    // 计算最终的裁剪空间位置
    gl_Position = vec4(aPosition, 1.0);
}
"""

liuguang_fragment = """
#version 330 core
uniform float time; // 时间变量，用于控制流光的动态效果

vec3 lightPos = vec3(0, 0, -2); // 光源位置
vec3 viewPos = vec3(0, 0, -1); // 观察者位置
vec3 lightColor = vec3(0.2, 0.2, 0.2); // 光源颜色

in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
in vec3 FragPos; // 从顶点着色器传递的片段位置
in vec3 Normal; // 从顶点着色器传递的法线

out vec4 FragColor;

// 镜面反射计算（Blinn-Phong模型）
vec3 calculateSpecular(vec3 normal, vec3 lightDir, vec3 viewDir) {
    vec3 halfVec = normalize(lightDir + viewDir); // 半角向量
    float spec = pow(max(dot(normal, halfVec), 0.0), 64); // 镜面反射强度
    return spec * lightColor; // 镜面反射光
}

void main() {
    // 流光效果的动态噪声
    vec2 uv = vTexCoord * 0.1 + vec2(time * 0.8, time * 0.3); // 缩放和时间偏移

    // 流光动态变化
    float flow = smoothstep(0.1, 0.5, sin(uv.x * 5.0 + uv.y * 5.0 + time * 2.0));

    // 镜面反射计算
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 specular = calculateSpecular(norm, lightDir, viewDir);

    // 最终颜色：镜面反射与流光效果的结合
    vec3 finalColor = specular * flow * 2.0; // 镜面反射与流光的动态结合
    FragColor = vec4(finalColor, 1.0);
}
"""

liuxing_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
out vec2 vTexCoord;
uniform float time;
uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

liuxing_fragment = """
#version 330 core
#define NUM_OCTAVES 5
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
in vec3 vColor;
uniform sampler2D texture0; // 纹理采样器
uniform float time;
uniform vec2 resolution;
out vec4 FragColor;

float rand(vec2 n) {
    return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 ip = floor(p);
    vec2 u = fract(p);
    u = u * u * (3.0 - 2.0 * u);
    float res = mix(
        mix(rand(ip), rand(ip + vec2(1.0, 0.0)), u.x),
        mix(rand(ip + vec2(0.0, 1.0)), rand(ip + vec2(1.0, 1.0)), u.x),
        u.y);
    return res * res;
}

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100);
    mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
    for (int i = 0; i < NUM_OCTAVES; ++i) {
        v += a * noise(x);
        x = rot * x * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 shake = vec2(sin(time * 1.5) * 0.01, cos(time * 2.7) * 0.01);
    vec2 fragCoord = vTexCoord * resolution;

    vec2 p = ((fragCoord + shake * resolution) - resolution * 0.5) / resolution.y;
    p *= mat2(8.0, -6.0, 6.0, 8.0);

    vec2 v;
    vec4 o = vec4(0.0);
    float f = 3.0 + fbm(p + vec2(time * 7.0, 0.0));

    for (float i = 0.0; i < 50.0; i++) {
        v = p + cos(i * i + (time + p.x * 0.1) * 0.03 + i * vec2(11.0, 9.0)) * 5.0
            + vec2(sin(time * 4.0 + i) * 0.005, cos(time * 4.5 - i) * 0.005);

        float tailNoise = fbm(v + vec2(time, i)) * (1.0 - (i / 50.0));
        vec4 currentContribution = (cos(sin(i) * vec4(1.0, 2.0, 3.0, 1.0)) + 1.0)
            * exp(sin(i * i + time)) / length(max(v, vec2(v.x * f * 0.02, v.y)));

        float thinnessFactor = smoothstep(0.0, 1.0, i / 50.0);
        o += currentContribution * (1.0 + tailNoise * 2.0) * thinnessFactor;
    }

    o = tanh(pow(o / 1e2, vec4(1.5)));
    FragColor = texture(texture0, vTexCoord);
    FragColor.xz = FragColor.zx;
    FragColor += o;
}
"""

miaobian_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;
out vec2 vTexCoord;
uniform float time;
uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

miaobian_fragment = """
#version 330 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标

uniform sampler2D texture0; // 纹理采样器
uniform float time;
out vec4 FragColor;

void main() {
    vec4 center = texture(texture0, vTexCoord);
    vec4 left = texture(texture0, vTexCoord + vec2(-0.01, 0.0));
    vec4 right = texture(texture0, vTexCoord + vec2(0.01, 0.0));
    vec4 top = texture(texture0, vTexCoord + vec2(0.0, 0.01));
    vec4 bottom = texture(texture0, vTexCoord + vec2(0.0, -0.01));
    vec4 edge = (left + right + top + bottom) * 0.2;
    FragColor = center + edge;
} 
"""

fanse_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
out vec2 vTexCoord;

void main() {
    gl_Position = vec4(aPosition, 1.0);
    vTexCoord = aTexCoord;
}
"""

fanse_fragment = """
#version 330 core
in vec2 vTexCoord; // 从顶点着色器传入的纹理坐标
uniform sampler2D texture0; // 纹理采样器
out vec4 FragColor;

void main() {    
    FragColor = 1 - texture(texture0, vTexCoord); 
}
"""

jiya_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;
out vec2 vTexCoord;
out vec3 vColor;
uniform float time;

out vec3 FragPos; // 传递到片段着色器的片段位置

void main() {
    // 挤压系数 (0.5为挤压50%)
    float squashFactor = 0.5 + sin(time * 5) * 0.5; 

    // 创建挤压矩阵
    vec3 scale = vec3(1 + squashFactor, 1 - squashFactor, 1 + squashFactor);
    vec4 pos = vec4(aPosition.xyz * scale, 1.0);

    gl_Position = pos;
    vTexCoord = aTexCoord;
}
"""

jiya_fragment = """
#version 330 core
in vec3 vColor;
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标
in vec3 FragPos; // 从顶点着色器传递的片段位置

uniform sampler2D texture0; // 纹理采样器
uniform float time;
out vec4 FragColor;

void main() {
    FragColor = texture(texture0, vTexCoord);
    FragColor.xz = FragColor.zx;
}
"""

xuancai_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;
out vec2 vTexCoord;
uniform float time;
uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

xuancai_fragment = """
#version 330 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标

uniform sampler2D texture0; // 纹理采样器
uniform float time;

out vec4 FragColor;

// 噪声函数（用于雾效）
float noise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453);
}

float fbm(vec3 p) {
    float sum = 0.0;
    float amp = 1.0;
    for(int i=0; i<5; i++) {
        sum += amp * noise(p.xy);
        amp *= 0.5;
        p = p*2.0 + vec3(100);
    }
    return sum;
}

vec3 nebula(vec3 rd) {
    vec3 pos = vec3(0);
    vec3 col = vec3(0);
    for(int i=0; i<64; i++) {
        float density = fbm(pos * 0.1);
        if(density > 0.2) {
            vec3 emission = sin(pos*0.5) * 0.5 + 0.5;
            col.rgb += emission * density * exp(-0.1*float(i));
        }
        pos += rd * 0.1;
    }
    return col;
}

void main() {
    vec2 uv = vTexCoord;

    // FragColor = texture2D(texture0, vTexCoord);
    FragColor = vec4(nebula(texture2D(texture0, vTexCoord).xyz), 1) * 0.15;
} 
"""

caiguangdeng_vertex = """
#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec2 aTexCoord;
layout(location = 2) in vec3 aRotPos;
out vec2 vTexCoord;
uniform float time;
uniform int off_screen;

void main() {
    gl_Position = vec4(aPosition, 1.0);

    vTexCoord = aTexCoord;
    if(off_screen == 0){
        vTexCoord.y = 1 - vTexCoord.y;
    }
}
"""

caiguangdeng_fragment = """
#version 330 core
in vec2 vTexCoord; // 从顶点着色器传递的纹理坐标

uniform sampler2D texture0; // 纹理采样器
uniform float time;
out vec4 FragColor;

void main() {
    vec2 uv = vTexCoord;

    vec3 col = vec3(0.0);

    float n_time = time;

    // 旋转矩阵
    uv *= mat2(cos(n_time), -sin(n_time), sin(n_time), cos(n_time));

    // 脉冲颜色
    float pulse = sin(n_time * 3.0) * 0.5 + 0.5;
    col += smoothstep(0.0, 1, abs(uv.x)) * vec3(pulse, 0.5, 1.0 - pulse);
    col += smoothstep(0.0, 1, abs(uv.y)) * vec3(1.0 - pulse, pulse, 0.3);

    FragColor = texture2D(texture0, vTexCoord);
    FragColor.xz = FragColor.zx;
    FragColor.xyz += col;
} 
"""