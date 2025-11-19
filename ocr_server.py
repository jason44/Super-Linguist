import socket
import struct
import json
import numpy as np
import matplotlib.pyplot as plt
#from PIL import Image, ImageTk
#import tkinter as tk
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    #lang="en",
    ocr_version="PP-OCRv5",
    device="gpu",
)

def recv_exact(sock, size):
    """Receive exactly 'size' bytes."""
    buf = b''
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("Client disconnected")
        buf += chunk
    return buf

def start_ocr_server(host="127.0.0.1", port=5000):
    # --- Setup socket ---
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of address
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen(1)
    print(f"Server listening on {host}:{port}")
    
    while True:
        try:
            conn, addr = server.accept()
            print("Client connected:", addr)

            while True:
                # Metadata: width, height, frame_size | 32-bit float
                header = recv_exact(conn, 12)
                width, height, frame_size = struct.unpack("<III", header)
                #print(width, height, frame_size)

                # --- Receive Pixbuf ---
                frame_bytes = recv_exact(conn, frame_size)
                frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((height, width, 3)) # RGB

                #plt.imshow(frame)
                #plt.show()

                # --- Send OCR results to client ---
                result = ocr.predict(frame)
                texts = []
                scores = []
                character_boxes = []
                print(result)

                for res in result[:1]:
                    texts.extend(res['rec_texts'])
                    scores.extend(res['rec_scores'])
                    character_boxes.extend(res['rec_boxes']) 

                return_data = {
                    'texts': texts, 
                    'scores': scores,
                    'character_level_boxes': [box.tolist() for box in character_boxes]
                }
                conn.send(json.dumps(return_data).encode('utf-8'))
                
                    
        except ConnectionError:
            print("Client disconnected, waiting for reconnection...")
            conn.close()
        except KeyboardInterrupt:
            conn.close()
            server.close()
            print("Server Shutdown.")
            break



"""
    # --- Prepare GUI window ---
    root = tk.Tk()
    root.title("Pixbuf Viewer")

    label = tk.Label(root)
    label.pack()

    def update_frame():
        try:
            # --- Receive metadata ---
            # Metadata: width, height, frame_size | 32-bit float
            header = recv_exact(conn, 12)
            width, height, frame_size = struct.unpack("<III", header)
            print(width, height, frame_size)

            # --- Receive Pixbuf ---
            frame_bytes = recv_exact(conn, frame_size)
            img = Image.frombytes("RGBA", (width, height), frame_bytes) # or RGBA?
            tk_img = ImageTk.PhotoImage(img)
            label.config(image=tk_img)
            label.image = tk_img

            # Resize the window to match the incoming image
            root.geometry(f"{width}x{height}")

            # Schedule the next frame update ASAP
            root.after(1, update_frame)

        except Exception as e:
            print("Stream ended:", e)
            root.destroy()

    # Start streaming
    root.after(1, update_frame)
    root.mainloop()
"""


if __name__ == "__main__":
    start_ocr_server()
