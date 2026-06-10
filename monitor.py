#!/usr/bin/env python3
import socket
import threading
import tkinter as tk
import requests
import time
import psutil
import sys
import json
import platform
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# Telegram config
TOKEN = ""
CHAT_ID = "" 
TEMP_THRESHOLD = 80.0  

# Get temperature data
def get_temperature_data():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None, "No temperature sensors detected."

        max_temp = 0.0
        report = ""
        
        for name, sensors in temps.items():
            report += f"- Sensor: {name}\n"
            for sensor in sensors:
                label = sensor.label or "General"
                report += f"   ├─ {label}: {sensor.current:.1f} °C\n"
                if sensor.current > max_temp:
                    max_temp = sensor.current
            report += "\n"
            
        return max_temp, report.strip()
    except Exception as e:
        return None, f"Error getting temperature: {e}"

# Get system info
def get_system_info():
    distro = "Unknown"
    
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
            
    if distro == "Unknown":
        distro = f"{platform.system()} {platform.release()}"

    cpu_model = platform.processor()
    if not cpu_model and os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu_model = line.split(":")[1].strip()
                        break
        except Exception:
            pass
            
    if not cpu_model:
        cpu_model = f"CPU x{psutil.cpu_count(logical=True)}"

    return {
        "os": distro,
        "kernel": platform.release(),
        "cpu": cpu_model,
        "arch": platform.machine()
    }

# Get local IP
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

# Send Telegram alert
def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram not configured.")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Monitor loop
def temperature_monitor():
    print("Temperature monitor started...")
    while True:
        try:
            temp_num, _ = get_temperature_data()
            if temp_num and temp_num > TEMP_THRESHOLD:
                send_telegram(f"🚨 Alert! Critical temperature: {temp_num}°C")
        except Exception as e:
            print(f"Monitor error: {e}")
        time.sleep(30) 

# Web server handler
class WebMonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Render HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            sys_info = get_system_info()
            
            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Server Monitor</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
                    h1 {{ color: #bb86fc; text-align: center; }}
                    .container {{ max-width: 800px; margin: auto; }}
                    .card {{ background-color: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                    .card h2 {{ margin-top: 0; color: #03dac6; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                    pre {{ background-color: #2c2c2c; padding: 15px; border-radius: 5px; color: #4caf50; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin-bottom: 15px; font-size: 1.1em; background-color: #252525; padding: 10px; border-radius: 5px; }}
                    .fastfetch-list li {{ background-color: transparent; margin-bottom: 5px; padding: 5px; font-size: 1em; }}
                    .sys-info-title {{ color: #ff0266; font-weight: bold; font-family: monospace; font-size: 1.2em; text-align: center; margin-bottom: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Server Status</h1>
                    
                    <div class="card">
                        <div class="sys-info-title">Neofetch / Fastfetch summary</div>
                        <ul class="fastfetch-list">
                            <li><b>OS:</b> {sys_info['os']}</li>
                            <li><b>Kernel:</b> {sys_info['kernel']}</li>
                            <li><b>CPU:</b> {sys_info['cpu']}</li>
                            <li><b>Arch:</b> {sys_info['arch']}</li>
                        </ul>
                    </div>

                    <div class="card">
                        <h2>Temperature Sensors</h2>
                        <pre id="temp-data">Loading...</pre>
                    </div>

                    <div class="card">
                        <h2>System Resources</h2>
                        <ul>
                            <li><b>Processor (CPU):</b> <span id="cpu-usage">0</span>%</li>
                            <li><b>RAM Memory:</b> <span id="ram-usage">0</span>% <span id="ram-detail" style="font-size: 0.9em; color: #aaa;"></span></li>
                        </ul>
                        
                        <h3 style="color: #03dac6; margin-top: 20px; border-bottom: 1px solid #333; padding-bottom: 10px;">Storage</h3>
                        <ul id="disk-list">
                            <li>Loading disks...</li>
                        </ul>
                    </div>
                </div>

                <script>
                    async function updateData() {{
                        try {{
                            const res = await fetch('/api/data');
                            const data = await res.json();

                            document.getElementById('temp-data').textContent = data.temperatures;
                            document.getElementById('cpu-usage').textContent = data.cpu_usage;
                            document.getElementById('ram-usage').textContent = data.ram_usage;
                            document.getElementById('ram-detail').textContent = '(' + data.ram_used_mb + ' MB / ' + data.ram_total_mb + ' MB)';

                            let disksHTML = '';
                            data.disks.forEach(d => {{
                                disksHTML += `<li><b>Disk ${{d.mount}}:</b> ${{d.percentage}}% <span style="font-size: 0.9em; color: #aaa;">(${{d.used}} GB / ${{d.total}} GB)</span></li>`;
                            }});
                            document.getElementById('disk-list').innerHTML = disksHTML;

                        }} catch (error) {{
                            console.error('Error fetching data:', error);
                        }}
                    }}
                    
                    setInterval(updateData, 5000); 
                    updateData(); 
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/api/data':
            # API endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            _, temp_report = get_temperature_data()
            cpu_usage = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            
            # Read system stats
            disk_data = []
            for part in psutil.disk_partitions(all=False):
                if part.fstype in ('', 'squashfs', 'tmpfs', 'devtmpfs', 'overlay', 'proc', 'sysfs'):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_data.append({
                        "mount": part.mountpoint,
                        "percentage": usage.percent,
                        "used": usage.used // (1024**3),
                        "total": usage.total // (1024**3)
                    })
                except PermissionError:
                    continue
            
            # Build JSON
            data = {
                "temperatures": temp_report if temp_report else "No sensors detected.",
                "cpu_usage": cpu_usage,
                "ram_usage": ram.percent,
                "ram_used_mb": ram.used // (1024**2),
                "ram_total_mb": ram.total // (1024**2),
                "disks": disk_data
            }
            
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_error(404, "Page not found")

    # Disable logs
    def log_message(self, format, *args):
        pass

# Start HTTP server
def start_server(port):
    HOST = "0.0.0.0"
    local_ip = get_ip()
    try:
        server = HTTPServer((HOST, port), WebMonitorHandler)
        print(f"HTTP Server listening on http://{local_ip}:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"Fatal error in HTTP server: {e}")

# Main GUI
def main_gui():
    root = tk.Tk()
    root.title("Linux Monitor")
    root.geometry("350x150")
    root.resizable(False, False)

    ip = get_ip()
    port = 54001  

    tk.Label(root, text="SERVER STATUS", font=("Arial", 10, "bold")).pack(pady=5)
    tk.Label(root, text=f"Local IP: {ip}").pack()
    tk.Label(root, text=f"Port: {port}").pack()
    
    lbl_status = tk.Label(root, text="Web Service Active", fg="green")
    lbl_status.pack(pady=10)

    send_telegram(f"Web Server successfully started at http://{ip}:{port}")
    
    threading.Thread(target=start_server, args=(port,), daemon=True).start()
    threading.Thread(target=temperature_monitor, daemon=True).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit()

if __name__ == "__main__":
    main_gui()