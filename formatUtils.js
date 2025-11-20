
export function i420ToRgb(data, width, height) {
    const stride = 3
    const rgb = new Uint8Array(width * height * stride);
    const ySize = width * height;
    const uSize = (width / 2) * (height / 2);

    const yData = data.subarray(0, ySize);
    const uData = data.subarray(ySize, ySize + uSize);
    const vData = data.subarray(ySize + uSize, ySize + uSize + uSize);

    for (let i = 0; i < width * height; i++) {
        const y = yData[i];
        const uIdx = Math.floor((i % width) / 2) + Math.floor(i / width / 2) * (width / 2);
        const u = uData[uIdx];
        const v = vData[uIdx];

        const r = Math.max(0, Math.min(255, y + 1.402 * (v - 128)));
        const g = Math.max(0, Math.min(255, y - 0.344136 * (u - 128) - 0.714136 * (v - 128)));
        const b = Math.max(0, Math.min(255, y + 1.772 * (u - 128)));

        rgb[i * stride] = r;
        rgb[i * stride + 1] = g;
        rgb[i * stride + 2] = b;
    }

    return rgb;
}

export function nv12ToRgb(data, width, height) {
    const stride = 3;
    const rgb = new Uint8Array(width * height * stride);
    const ySize = width * height;
    const uvSize = (width * height) >> 1; // width * height / 2

    const yData = data.subarray(0, ySize);
    const uvData = data.subarray(ySize, ySize + uvSize);

    const uvStride = width; // each UV row has width bytes (U,V pairs)

    for (let y = 0; y < height; y++) {
        const yRow = y * width;
        const uvRow = Math.floor(y / 2) * uvStride;
        for (let x = 0; x < width; x++) {
    const yi = yRow + x;
    const uvIndex = uvRow + (Math.floor(x / 2) * 2); // U then V
    const Y = yData[yi];
    const U = uvData[uvIndex];
    const V = uvData[uvIndex + 1];

    const r = Math.max(0, Math.min(255, Y + 1.402 * (V - 128)));
    const g = Math.max(0, Math.min(255, Y - 0.344136 * (U - 128) - 0.714136 * (V - 128)));
    const b = Math.max(0, Math.min(255, Y + 1.772 * (U - 128)));

    const outIdx = yi * stride;
    rgb[outIdx] = r;
    rgb[outIdx + 1] = g;
    rgb[outIdx + 2] = b;
        }
    }

    return rgb;
}