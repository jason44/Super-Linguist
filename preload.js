const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('superLinguist', {
    ocrRequest: (metadata, pixbuf) => ipcRenderer.send('ocr-request', metadata, pixbuf),
    getOcrOutput: () => ipcRenderer.sendSync('get-ocr-output'),
    onOcrOutputChanged: (callback) => {
        ipcRenderer.on("ocr-output-changed", (_, value) => callback(value))
    }
})