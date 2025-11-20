const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('superLinguist', {
    print: (str) => ipcRenderer.send('print', str),
    sendOcrRequest: (metadata, pixbuf) => ipcRenderer.send('ocr-request', metadata, pixbuf),
    getOcrOutput: () => ipcRenderer.sendSync('get-ocr-output'), // UNUSED
    onOcrOutputChanged: (callback) => 
        ipcRenderer.on("ocr-output-changed", async (_, value) => 
            callback(value)),
    createCaptionWindow: (width, height, data) => ipcRenderer.send('create-caption-window', width, height, data), // synchronous because the async part will be the onChanged functions
    updateCaptionWindow: () => ipcRenderer.send('update-caption-window'), // synchronous
    captionWindowExists: () => ipcRenderer.sendSync('caption-window-exists'),
    closeCaptionWindow: () => ipcRenderer.send('close-caption-window'),
    onCaptionWindowDimensionsChanged: (callback) => 
        ipcRenderer.on("caption-window-dimensions-changed", async (_, width, height) => 
            callback(width, height)),
    onCaptionWindowContentChanged: (callback) => 
        ipcRenderer.on("caption-window-content-changed", async (_, data) => 
            callback(data)),
})