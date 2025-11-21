import socket
import struct
import json
import numpy as np
import matplotlib.pyplot as plt
#from PIL import Image, ImageTk
#import tkinter as tk
from paddleocr import PaddleOCR
import utils.language_processor as lang

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    #lang="en",
    ocr_version="PP-OCRv4",
    device="gpu",
)

prev_ocr_key = ""
def is_same_frame(ocr_key):
    if ocr_key == prev_ocr_key: return True
    return False


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
        conn = None
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
                res = ocr.predict(frame)
                #print(result)

                rec_thres = 0.85
                data = { 'texts': [], 'boxes': [] }
                for i in range(res[0]['rec_texts']):
                    if res[0]['rec_scores'][i] > rec_thres:
                        data['texts'].append(res[0]['rec_texts'][i])
                        data['boxes'].append(res[0]['rec_boxes'][i].tolist())

                # Do not update if the ocr results do not change 
                cur_ocr_key = "".join(data['texts']).strip()
                if is_same_frame(): continue
                prev_ocr_key = cur_ocr_key

                # Group lines and split into words
                data = lang.group_lines(data)
                data['texts'] = lang.batch_split_to_words(data['texts'])

                conn.send(json.dumps(data).encode('utf-8'))
        except ConnectionError:
            print("Client disconnected, waiting for reconnection...")
            conn.close()
        except KeyboardInterrupt:
            if conn: conn.close()
            server.close()
            print("Server Shutdown Successfully.")
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
