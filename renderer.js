
document.addEventListener('DOMContentLoaded', () => {
  const cropFrame = document.getElementById('cropFrame');
  const video = document.getElementById('screenCapture');
  const container = document.querySelector('.crop-container');
  const selectButton = document.getElementById('selectButton')
  const stopButton = document.getElementById('stopButton')
  const info = document.getElementById('info'); // debug
  const textBox = document.getElementById('textBox'); // debug

  // --- Updated Handle Selection ---
  const handles = document.querySelectorAll('.resize-handle');

  let isDragging = false;
  let isResizing = false;
  let resizeDirection = ''; // Store which handle is being used
  let startX, startY, startLeft, startTop, startWidth, startHeight;
  let videoWidth, videoHeight;

  const minSize = 32; // Minimum crop size

  function updateVideoBounds() {
    videoWidth = video.clientWidth;
    videoHeight = video.clientHeight;

    // Protect against zero-size video
    if (!videoWidth || !videoHeight) return;

    const cropFrameWidth = cropFrame.offsetWidth;
    const cropFrameHeight = cropFrame.offsetHeight;
    let left = cropFrame.offsetLeft;
    let top = cropFrame.offsetTop;

    // Ensure cropFrame dimensions do not exceed video dimensions
    const newWidth = Math.min(cropFrameWidth, videoWidth);
    const newHeight = Math.min(cropFrameHeight, videoHeight);

    // Compute max allowed top/left so the cropFrame stays fully inside the video
    const maxLeft = Math.max(0, videoWidth - newWidth);
    const maxTop = Math.max(0, videoHeight - newHeight);

    left = Math.max(0, Math.min(left, maxLeft));
    top = Math.max(0, Math.min(top, maxTop));

    cropFrame.style.width = newWidth + 'px';
    cropFrame.style.height = newHeight + 'px';
    cropFrame.style.left = left + 'px';
    cropFrame.style.top = top + 'px';
  }

  window.addEventListener('resize', updateVideoBounds);
  video.addEventListener('resize', updateVideoBounds);

  // --- 1. Dragging Logic (unchanged) ---
  cropFrame.addEventListener('mousedown', (e) => {
    // Only drag if mousedown is on the cropFrame itself, not a handle
    if (e.target.classList.contains('resize-handle')) {
      return;
    }

    e.preventDefault();
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    startLeft = cropFrame.offsetLeft;
    startTop = cropFrame.offsetTop;
  });

  // --- Resizing Logic (Updated for all handles) ---
  handles.forEach(handle => {
    handle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      e.stopPropagation(); // Stop mousedown from bubbling to the cropFrame

      isResizing = true;
      // Store the direction from the data-attribute
      resizeDirection = handle.dataset.direction;

      startX = e.clientX;
      startY = e.clientY;
      startLeft = cropFrame.offsetLeft;
      startTop = cropFrame.offsetTop;
      startWidth = cropFrame.offsetWidth;
      startHeight = cropFrame.offsetHeight;
    });
  });

  // --- Global Mouse Move Handler (Updated for resizing) ---
  document.addEventListener('mousemove', (e) => {
    if (isDragging) {
      // Drag logic (unchanged)
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      let newLeft = startLeft + dx;
      let newTop = startTop + dy;

      newLeft = Math.max(0, Math.min(newLeft, videoWidth - cropFrame.offsetWidth));
      newTop = Math.max(0, Math.min(newTop, videoHeight - cropFrame.offsetHeight));

      cropFrame.style.left = newLeft + 'px';
      cropFrame.style.top = newTop + 'px';

    } else if (isResizing) {
      // --- New Resizing Logic ---
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;

      let newLeft = startLeft;
      let newTop = startTop;
      let newWidth = startWidth;
      let newHeight = startHeight;

      // Calculate new dimensions based on handle direction
      switch (resizeDirection) {
        case 'se':
          newWidth = startWidth + dx;
          newHeight = startHeight + dy;
          break;
        case 'sw':
          newWidth = startWidth - dx;
          newHeight = startHeight + dy;
          newLeft = startLeft + dx;
          break;
        case 'ne':
          newWidth = startWidth + dx;
          newHeight = startHeight - dy;
          newTop = startTop + dy;
          break;
        case 'nw':
          newWidth = startWidth - dx;
          newHeight = startHeight - dy;
          newLeft = startLeft + dx;
          newTop = startTop + dy;
          break;
      }

      // --- Constraint Checks ---

      // 1. Minimum Size (width)
      if (newWidth < minSize) {
        if (resizeDirection === 'nw' || resizeDirection === 'sw') {
          newLeft = startLeft + startWidth - minSize;
        }
        newWidth = minSize;
      }

      // 2. Minimum Size (height)
      if (newHeight < minSize) {
        if (resizeDirection === 'nw' || resizeDirection === 'ne') {
          newTop = startTop + startHeight - minSize;
        }
        newHeight = minSize;
      }

      // 3. Image Boundaries
      // Left boundary
      if (newLeft < 0) {
        if (resizeDirection === 'nw' || resizeDirection === 'sw') {
          newWidth += newLeft; // newLeft is negative
        }
        newLeft = 0;
      }
      // Top boundary
      if (newTop < 0) {
        if (resizeDirection === 'nw' || resizeDirection === 'ne') {
          newHeight += newTop; // newTop is negative
        }
        newTop = 0;
      }
      // Right boundary
      if (newLeft + newWidth > videoWidth) {
        newWidth = videoWidth - newLeft;
      }
      // Bottom boundary
      if (newTop + newHeight > videoHeight) {
        newHeight = videoHeight - newTop;
      }

      // Re-check min size post-boundary constraint
      newWidth = Math.max(minSize, newWidth);
      newHeight = Math.max(minSize, newHeight);

      // Apply the new styles
      cropFrame.style.left = newLeft + 'px';
      cropFrame.style.top = newTop + 'px';
      cropFrame.style.width = newWidth + 'px';
      cropFrame.style.height = newHeight + 'px';
    }
  });

  // --- Global Mouse Up Handler ---
  document.addEventListener('mouseup', () => {
    isDragging = false;
    isResizing = false;
    resizeDirection = '';

    info.innerHTML = `Client Video Size: ${videoWidth} x ${videoHeight}<br>
        Real Video Size: ${video.videoWidth} x ${video.videoHeight}<br>
        cropFrame Position: (${(cropFrame.offsetLeft / videoWidth).toFixed(2)}, ${(cropFrame.offsetTop / videoHeight).toFixed(2)})<br>
        cropFrame Size: ${(cropFrame.offsetWidth / videoWidth).toFixed(2)} x ${(cropFrame.offsetHeight / videoHeight).toFixed(2)}<br>
        Real cropFrame Position: (${Math.round(cropFrame.offsetLeft / videoWidth * video.videoWidth)}, ${Math.round(cropFrame.offsetTop / videoHeight * video.videoHeight)})<br>
        Real cropFrame Size: ${Math.round(cropFrame.offsetWidth / videoWidth * video.videoWidth)} x ${Math.round(cropFrame.offsetHeight / videoHeight * video.videoHeight)}`;
  });

  // --- Select and Stop Button Logic ---
  selectButton.addEventListener('click', () => {
    navigator.mediaDevices.getDisplayMedia({
      audio: false,
      video: {
        frameRate: 2 // too high will cause high idle power consumption
      }
    }).then(stream => {
      video.srcObject = stream;

      const track = stream.getVideoTracks()[0];
      track.applyConstraints({
        cursor: false
      })
      const processor = new MediaStreamTrackProcessor({ track });
      const reader = processor.readable.getReader();

      // -- Send cropped frame to socket
      function calculateNormRect() {
        return {
          pos: [(cropFrame.offsetLeft / videoWidth), (cropFrame.offsetTop / videoHeight)],
          size: [(cropFrame.offsetWidth / videoWidth), (cropFrame.offsetHeight / videoHeight)]
        }
      }

      function i420ToRgb(data, width, height) {
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

      async function readFrame() {
        const result = await reader.read();
        if (result.done) return;

        const frame = result.value; // VideoFrame

        // Get raw bytes
        const data = new Uint8Array(frame.allocationSize());
        await frame.copyTo(data);

        // Convert I420 to RGB
        let rgbData;
        if (frame.format == 'I420') {
          rgbData = i420ToRgb(data, frame.displayWidth, frame.displayHeight);
        } else {
          rgbData = data;
        }

        // Crop using normalized rectangle
        const rect = calculateNormRect();
        const cropLeft = Math.round(frame.displayWidth * rect.pos[0]);
        const cropTop = Math.round(frame.displayHeight * rect.pos[1]);
        const cropWidth = Math.round(frame.displayWidth * rect.size[0]);
        const cropHeight = Math.round(frame.displayHeight * rect.size[1]);

        // Extract cropped pixels (RGB format, 3 bytes per pixel)
        const bytesPerPixel = 3;
        const stride = frame.displayWidth * bytesPerPixel;
        const croppedData = new Uint8Array(cropWidth * cropHeight * bytesPerPixel);

        for (let y = 0; y < cropHeight; y++) {
          const srcOffset = ((cropTop + y) * frame.displayWidth + cropLeft) * bytesPerPixel;
          const dstOffset = y * cropWidth * bytesPerPixel;
          croppedData.set(rgbData.slice(srcOffset, srcOffset + cropWidth * bytesPerPixel), dstOffset);
        }

        /*console.log(
            "cropFrame:",
            frame.displayWidth,
            frame.displayHeight,
            "cropped to:",
            cropWidth,
            cropHeight,
            "at pos:",
            cropLeft,
            cropTop,
            "bytes", rgbData.length,
            "cropped bytes:", croppedData.length
        ); */

        const metadata = new Uint32Array([frame.displayWidth, frame.displayHeight, rgbData.length])
        window.superLinguist.ocrRequest(metadata, rgbData)

        frame.close();
        readFrame();
      }

      readFrame();

      video.onloadedmetadata = (e) => {
        video.play()
        updateVideoBounds()
      }
    }).catch(e => console.log(e))
  })

  stopButton.addEventListener('click', () => {
    video.pause()
  })

});



