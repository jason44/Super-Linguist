import { app, BrowserWindow, desktopCapturer, session, ipcMain} from 'electron';
import { fileURLToPath } from 'url';
import path from 'path';
import net from 'net';

// Lift AppArmor restrictions:
// sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// -- OCR Server Connection
const HOST = 'localhost';
const PORT = 5000;

const ocrClient = new net.Socket();
let isConnected = false;
ocrClient.connect(PORT, HOST, () => {
  isConnected = true;
  console.log(`Connected to ${HOST}:${PORT}`);
});

let ocrOutput = {texts: [], scores: [], character_level_boxes: []}
ocrClient.on('data', (data) => {
  const res = JSON.parse(data);
  console.log(res)
  ocrOutput = res;
  win.webContents.send("ocr-output-changed", ocrOutput)

})

ocrClient.on('close', () => {
  console.log('Connection closed');
});

ocrClient.on('error', (err) => {
  console.error(`Socket error: ${err.message}`);
});



// --- IPC Main ---
ipcMain.on('ocr-request', async (event, metadata, pixbuf) => {
  ocrClient.write(metadata);
  ocrClient.write(pixbuf);
})

ipcMain.on('get-ocr-output', async (event) => {
  event.returnValue = ocrResults
})


let win;
app.whenReady().then(() => {
  // -- Main Window
  win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    }
  })
  win.loadFile('index.html')

  session.defaultSession.setDisplayMediaRequestHandler((request, callback) => {
    // types: ['screen', 'window']
    desktopCapturer.getSources({ types: ['window'] }).then((sources) => {
      const sourceWindow = new BrowserWindow({
      width: 400,
      height: 300,
      modal: true,
      parent: win
      });
      
      sourceWindow.loadURL(`data:text/html,
      <html>
        <body style="font-family: Arial; padding: 20px;">
        <h2>Select a window to capture:</h2>
        <select id="sourceSelect" style="width: 100%; padding: 8px; margin: 10px 0;">
          ${sources.map((source, i) => `<option value="${i}">${source.name}</option>`).join('')}
        </select>
        <button onclick="confirm()" style="padding: 8px 16px; margin-right: 8px;">OK</button>
        <button onclick="cancel()" style="padding: 8px 16px;">Cancel</button>
        <script>
          const { ipcRenderer } = require('electron');
          function confirm() { ipcRenderer.send('source-selected', parseInt(document.getElementById('sourceSelect').value)); window.close(); }
          function cancel() { window.close(); }
        </script>
        </body>
      </html>
      `);
      
      ipcMain.once('source-selected', (event, index) => {
        callback({ video: sources[index], audio: 'loopback' });
      });
    })
    // If true, use the system picker if available.
    // Note: this is currently experimental. If the system picker
    // is available, it will be used and the media request handler
    // will not be invoked.
  }, { useSystemPicker: true })

})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    ocrClient.end()
  }
})