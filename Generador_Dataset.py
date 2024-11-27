import cv2
import os
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox


# Nombre de las clases a clasificar
classes = [
    "Plastico",
    "Metal",
    "Aluminio",
    "Vidrio",
    "Papel",
    "Carton",
]

# Directorio donde se almacenarán las imágenes capturadas
directory = 'dataset'
# Crea el directorio si no existe
if not os.path.exists(directory):
    os.makedirs(directory)

# Función para guardar la imagen capturada
def save_image():
    # Selecciona la clase elegida
    class_name = class_var.get()
    if not class_name:
        messagebox.showwarning("Advertencia", "Debe seleccionar una clase antes de capturar una imagen.")
        return

    # Configura el directorio de la clase a capturar
    class_directory = os.path.join(directory, class_name)
    try:
        if not os.path.exists(class_directory):
            os.makedirs(class_directory)
    except OSError:
        print(f"No se pudo crear el directorio {class_directory}")
        exit()

    # Recorre las imágenes existentes y encuentra el número más alto
    existing_images = os.listdir(class_directory)
    if existing_images:
        last_image = sorted(existing_images, key=lambda x: int(x.split('_')[-1].split('.')[0]))[-1]
        last_number = int(last_image.split('_')[-1].split('.')[0])
    else:
        last_number = 0

    # Captura la imagen actual
    ret, frame = cap.read()
    
    # Genera el nombre de la imagen según la clase y el número más alto
    filename = f"{class_name}_{str(last_number+1)}.jpg"
        
    # Guarda la imagen en el directorio correspondiente
    cv2.imwrite(os.path.join(class_directory, filename), frame)

    filename_var.set(f"Imagen guardada: {class_directory}\{filename}")
    print(f"Imagen guardada {class_directory}\{filename}")
    
    # Actualiza la última imagen capturada
    last_image = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    last_image_label.config(image=last_image, text= filename)
    last_image_label.image = last_image

    # Actualiza la imagen del widget de imagen con la imagen actual
    img = Image.open(os.path.join(class_directory, filename))
    # img = img.resize((640, 480), resample=Image.LANCZOS)
    img = ImageTk.PhotoImage(img)
    image_label.config(image=img)
    image_label.image = img

def update_image(image_label):
    ret, frame = cap.read()
    if ret:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(img))

        # Actualiza la imagen capturada en el widget de imagen de la interfaz
        image_label.config(image=img)
        image_label.image = img
    # Programar la función para que se llame de nuevo después de 10 milisegundos
    image_label.after(10, update_image, image_label)


# Inicia la captura de la cámara
# cap = cv2.VideoCapture("192.168.1.7:81/stream")
# cap = cv2.VideoCapture("http://192.168.196.2:81/stream")
cap = cv2.VideoCapture("http://192.168.1.13:81/stream")
# cap = cv2.VideoCapture(0)

# Crea la ventana principal de la interfaz
root = tk.Tk()
root.geometry("1200x650")
root.state('zoomed')
root.title("Capturador de imágenes")
root.iconbitmap("C:/Users/Mariano/Desktop/Proyecto_Final/Python/.venv/UTN_16.ico")
# icono_chico = tk.PhotoImage(file="C:/Users/Mariano/Desktop/Proyecto_Final/Python/.venv/UTN_16.ico")
# icono_grande = tk.PhotoImage(file="C:/Users/Mariano/Desktop/Proyecto_Final/Python/.venv/UTN_32.ico")
# root.iconphoto(False, icono_grande, icono_chico)
root.config(bg="#1E90FF")

fuente = "Comic Sans MS"

# Etiqueta para la seleccion de clase
class_label = tk.Label(root, text="Seleccione la clase a capturar:", font=(fuente, 15), background="#1E90FF")
class_label.grid(column=0, row=0, ipadx=10, ipady=10)

# Menú de opciones desplegable
class_var = tk.StringVar()
class_combobox = ttk.Combobox(root, textvariable=class_var, values=classes, font=(fuente, 12), state="readonly")
class_combobox.grid(column=1, row=0, ipadx=5, ipady=5)

# Etiqueta imagen en tiempo real
image_text = tk.Label(root, background="#1E90FF", text="Imagen en tiempo real", font=(fuente, 12))
image_text.grid(column=0, row=1, ipadx=10, ipady=10, columnspan=2)

# Presentación de imagen en tiempo real
image_label = tk.Label(root, background="#1E90FF")
image_label.grid(column=0, row=2, ipadx=10, ipady=10, columnspan=2)

update_image(image_label)

# Etiqueta con nombre de la imagen guardada
filename_var = tk.StringVar()
last_image_text = tk.Label(root, background="#1E90FF", textvariable=filename_var, font=(fuente, 12))
last_image_text.grid(column=2, row=1, ipadx=10, ipady=10, columnspan=2)

# Presentación de la última captura
last_image_label = tk.Label(root, background="#1E90FF")
last_image_label.grid(column=2, row=2, ipadx=10, ipady=10, columnspan=2)

# Crea un botón para capturar la imagen
capture_button = tk.Button(root, text="Capturar imagen", font=(fuente, 15), command=save_image, background="#FFA500")
capture_button.grid(column=0, row=3, ipadx=10, ipady=10, columnspan=2)

# Vincular la tecla Enter al botón
root.bind('<Return>', lambda event=None: capture_button.invoke())

# Crea un botón para salir de la aplicación
quit_button = tk.Button(root, text="Salir", font=(fuente, 15), command=root.quit)
quit_button.grid(column=3, row=3, ipadx=10, ipady=10)

# Inicia el loop de la interfaz
root.mainloop()

# Libera los recursos utilizados
cap.release()
cv2.destroyAllWindows()