import numpy as np
from PIL import Image
import customtkinter as ctk  # Modern UI
from tkinter import filedialog, messagebox

# Function for Integer-based Haar Wavelet Transform
def integer_haar_transform(img):
    img = img.astype(np.int32)
    height, width = img.shape
    if height % 2 != 0:
        img = np.vstack([img, img[-1:, :]])
    if width % 2 != 0:
        img = np.hstack([img, img[:, -1:]])
    s = (img[:, 0::2] + img[:, 1::2]) // 2
    d = img[:, 0::2] - img[:, 1::2]
    LL = (s[0::2, :] + s[1::2, :]) // 2
    LH = s[0::2, :] - s[1::2, :]
    HL = (d[0::2, :] + d[1::2, :]) // 2
    HH = d[0::2, :] - d[1::2, :]
    return LL, (LH, HL, HH)

# Function for Inverse Haar Transform
def integer_haar_inverse(coeffs):
    LL, (LH, HL, HH) = coeffs
    s = np.zeros((LL.shape[0] * 2, LL.shape[1]), dtype=np.int32)
    d = np.zeros((HL.shape[0] * 2, HL.shape[1]), dtype=np.int32)
    s[0::2, :] = LL + (LH + 1) // 2
    s[1::2, :] = LL - LH // 2
    d[0::2, :] = HL + (HH + 1) // 2
    d[1::2, :] = HL - HH // 2
    img = np.zeros((s.shape[0], s.shape[1] * 2), dtype=np.int32)
    img[:, 0::2] = s + (d + 1) // 2
    img[:, 1::2] = s - d // 2
    return np.clip(img, 0, 255).astype(np.uint8)

# Embed Message into Image
def embed_message_dwt(image_path, message, output_path):
    image = Image.open(image_path).convert("L")
    img_array = np.array(image, dtype=np.int32)
    LL, (LH, HL, HH) = integer_haar_transform(img_array)
    LL_flat = LL.flatten()
    message_bin = ''.join(format(ord(c), '08b') for c in message) + '00000000'
    if len(message_bin) > LL_flat.size:
        raise ValueError("Message too large for LL subband")
    for i in range(len(message_bin)):
        LL_flat[i] = (LL_flat[i] & 0xFE) | int(message_bin[i])
    LL_modified = LL_flat.reshape(LL.shape)
    reconstructed = integer_haar_inverse((LL_modified, (LH, HL, HH)))
    Image.fromarray(reconstructed).save(output_path)
    return output_path

# Extract Message from Image
def extract_message_dwt(image_path):
    image = Image.open(image_path).convert("L")
    img_array = np.array(image, dtype=np.int32)
    LL, _ = integer_haar_transform(img_array)
    LL_flat = LL.flatten()
    extracted_bin = ''.join(str(byte & 1) for byte in LL_flat)
    message = ""
    for i in range(0, len(extracted_bin), 8):
        byte = extracted_bin[i:i + 8]
        if byte == '00000000':
            break
        message += chr(int(byte, 2))
    return message

# GUI Functions
def select_image():
    global image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if image_path:
        img = Image.open(image_path)
        img = ctk.CTkImage(light_image=img, size=(250, 250))
        image_label.configure(image=img)
        image_label.image = img

def embed_message():
    global image_path
    if not image_path:
        messagebox.showerror("Error", "Please select an image first")
        return
    message = message_entry.get()
    if not message:
        messagebox.showerror("Error", "Please enter a message to hide")
        return
    output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
    if not output_path:
        return
    try:
        embed_message_dwt(image_path, message, output_path)
        messagebox.showinfo("Success", f"Message embedded! Saved as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def extract_message():
    global image_path
    if not image_path:
        messagebox.showerror("Error", "Please select a stego image first")
        return
    try:
        extracted_message = extract_message_dwt(image_path)
        if extracted_message:
            messagebox.showinfo("Extracted Message", extracted_message)
        else:
            messagebox.showerror("Error", "No message found")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk()
root.title("DWT Image Steganography")
root.geometry("500x600")

frame = ctk.CTkFrame(root, corner_radius=10)
frame.pack(pady=20, padx=20, fill='both', expand=True)

ctk.CTkLabel(frame, text="DWT Image Steganography", font=("Arial", 18, "bold")).pack(pady=10)
image_label = ctk.CTkLabel(frame, text="No Image Selected", width=250, height=250, fg_color="gray")
image_label.pack(pady=10)

ctk.CTkButton(frame, text="Select Image", command=select_image).pack(pady=5)
message_entry = ctk.CTkEntry(frame, placeholder_text="Enter your message", width=300)
message_entry.pack(pady=5)
ctk.CTkButton(frame, text="Embed Message", command=embed_message, fg_color="green").pack(pady=5)
ctk.CTkButton(frame, text="Extract Message", command=extract_message, fg_color="orange").pack(pady=5)

root.mainloop()
