import tkinter as tk
from tkinter import messagebox, filedialog
import os
from datetime import datetime

def seleccionar_archivo():
    ruta = filedialog.askopenfilename(
        title="Selecciona el archivo de IANC_H2O a modificar",
        filetypes=[("Archivos Python", "*.py"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        lbl_archivo.config(text=ruta, fg="green")
        root.archivo_seleccionado = ruta

def aplicar_parche():
    archivo_target = getattr(root, 'archivo_seleccionado', None)
    
    if not archivo_target:
        messagebox.showwarning("Atención", "Primero debes seleccionar el archivo de destino.")
        return

    # Obtención de texto en modo RAW para preservar indentación exacta
    # "1.0" a "end-1c" evita que Tkinter añada un salto de línea invisible al final
    bloque_viejo = txt_viejo.get("1.0", "end-1c")
    bloque_nuevo = txt_nuevo.get("1.0", "end-1c")

    if not bloque_viejo or not bloque_nuevo:
        messagebox.showwarning("Atención", "Ambos campos de código son obligatorios.")
        return

    try:
        with open(archivo_target, "r", encoding="utf-8") as f:
            contenido_original = f.read()

        # Verificación de seguridad: El reemplazo solo ocurre si la coincidencia es total
        if bloque_viejo in contenido_original:
            # 1. Crear respaldo preventivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            respaldo = f"{archivo_target}_{timestamp}.bak"
            with open(respaldo, "w", encoding="utf-8") as bak:
                bak.write(contenido_original)
            
            # 2. Ejecutar el reemplazo exclusivo
            # Solo se altera la sección coincidente; el resto permanece intacto.
            nuevo_contenido = contenido_original.replace(bloque_viejo, bloque_nuevo)
            
            with open(archivo_target, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            
            messagebox.showinfo("Éxito", f"Reemplazo quirúrgico finalizado.\nRespaldo: {os.path.basename(respaldo)}")
            
            # Limpiar campos para evitar duplicidad accidental
            txt_viejo.delete("1.0", tk.END)
            txt_nuevo.delete("1.0", tk.END)
        else:
            messagebox.showerror("Error de Coincidencia", 
                "El bloque original no existe en el archivo exactamente como fue pegado.\n\n"
                "Asegúrese de no haber borrado espacios o tabulaciones al copiar.")
    except Exception as e:
        messagebox.showerror("Error Crítico", f"No se pudo modificar el archivo: {str(e)}")

# Interfaz Visual
root = tk.Tk()
root.title("Cirujano de Código IANC_H2O - V2.1 (Precisión Estricta)")
root.geometry("750x700")
root.configure(bg="#f4f4f4")
root.archivo_seleccionado = None

# Encabezado informativo
tk.Label(root, text="MODIFICADOR DE PRECISIÓN IANC_H2O", bg="#f4f4f4", font=("Arial", 12, "bold")).pack(pady=5)

# Sección de Selección
frame_archivo = tk.Frame(root, bg="#e0e0e0", bd=2, relief="groove")
frame_archivo.pack(pady=10, padx=20, fill="x")

tk.Label(frame_archivo, text="ARCHIVO DESTINO:", font=("Arial", 9, "bold"), bg="#e0e0e0").pack(side="left", padx=5)
lbl_archivo = tk.Label(frame_archivo, text="No seleccionado", font=("Arial", 9, "italic"), bg="#e0e0e0", fg="red")
lbl_archivo.pack(side="left", padx=5)
btn_buscar = tk.Button(frame_archivo, text="BUSCAR", command=seleccionar_archivo, bg="#5bc0de", fg="white")
btn_buscar.pack(side="right", padx=5, pady=5)

# Bloque Original
tk.Label(root, text="1. BLOQUE EXACTO A ELIMINAR (ORIGINAL):", font=("Arial", 10, "bold"), bg="#f4f4f4").pack(pady=5)
txt_viejo = tk.Text(root, height=12, width=85, font=("Consolas", 10), undo=True); txt_viejo.pack(padx=20)

# Bloque Nuevo
tk.Label(root, text="2. NUEVO BLOQUE A INSERTAR:", font=("Arial", 10, "bold"), bg="#f4f4f4").pack(pady=5)
txt_nuevo = tk.Text(root, height=12, width=85, font=("Consolas", 10), fg="blue", undo=True); txt_nuevo.pack(padx=20)

# Botón de ejecución
btn = tk.Button(root, text="APLICAR REEMPLAZO ÚNICO", command=aplicar_parche, 
                bg="#d9534f", fg="white", font=("Arial", 12, "bold"), cursor="hand2", pady=10)
btn.pack(pady=20)

root.mainloop()