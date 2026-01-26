#!/usr/bin/env python3
import socket
import threading
import tkinter as tk
import requests
import time
import psutil
import sys


TOKEN = ""
CHAT_ID = "" 
UMBRAL_TEMP = 80.0  



def obtener_datos_temperatura():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None, "No se detectaron sensores de temperatura."

        max_temp = 0.0
        reporte = ""
        
        for nombre, sensores in temps.items():
            reporte += f"- Sensor: {nombre}\n"
            for sensor in sensores:
                etiqueta = sensor.label or "General"
                reporte += f"   ├─ {etiqueta}: {sensor.current:.1f} °C\n"
                if sensor.current > max_temp:
                    max_temp = sensor.current
            reporte += "\n"
            
        return max_temp, reporte.strip()
    except Exception as e:
        return None, f"Error al obtener temperatura: {e}"






def obIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except:
        return "127.0.0.1"

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        print("Telegram no configurado.")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar mensaje de Telegram: {e}")









def monitor_temperatura():
    print("Monitor de temperatura iniciado...")
    while True:
        try:
            temp_num, _ = obtener_datos_temperatura()
            print(temp_num)
            if temp_num and temp_num > UMBRAL_TEMP:
                enviar_telegram(f"🚨 ¡Alerta! Temperatura crítica: {temp_num}°C")
        except Exception as e:
            print(f"Error en monitor: {e}")
        time.sleep(30) 

def iniciar_servidor(puerto):
    HOST = "0.0.0.0"
    ipLocal = obIP()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, puerto))
            s.listen()
            print(f"Servidor socket escuchando en {ipLocal}:{puerto}")
            while True:
                conn, addr = s.accept()
                with conn:
                    datos = conn.recv(1024).decode().strip()
                    if datos.startswith("temp"):
                        try:
                            partes = datos.split()

                            if len(partes) > 1 and partes[1] != ipLocal:
                                conn.sendall(b"IP no coincide.")
                            else:
                                _, reporte = obtener_datos_temperatura()
                                conn.sendall(reporte.encode())
                        except:
                            conn.sendall(b"Error al procesar comando.")
                    else:
                        conn.sendall(b"Comando desconocido. Use 'temp'.")
    except Exception as e:
        print(f"Error fatal en el servidor socket: {e}")










def main_gui():
    root = tk.Tk()
    root.title("Monitor Linux")
    root.geometry("350x150")
    root.resizable(False, False)

    ip = obIP()
    puerto = 54001  

    tk.Label(root, text="ESTADO DEL SERVIDOR", font=("Arial", 10, "bold")).pack(pady=5)
    tk.Label(root, text=f"IP Local: {ip}").pack()
    tk.Label(root, text=f"Puerto: {puerto}").pack()
    
    lbl_status = tk.Label(root, text="Servicio Activo ✅", fg="green")
    lbl_status.pack(pady=10)

    enviar_telegram(f"✅ Servidor iniciado correctamente en {ip}:{puerto}")
    
    threading.Thread(target=iniciar_servidor, args=(puerto,), daemon=True).start()
    threading.Thread(target=monitor_temperatura, daemon=True).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit()

if __name__ == "__main__":
    main_gui()