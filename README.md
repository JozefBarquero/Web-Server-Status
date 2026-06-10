README by: Gemini AI

# 🖥️ Linux Server Web Monitor

This project provides a lightweight, real-time web dashboard and GUI to monitor a Linux server's health. It tracks temperature, CPU, RAM, and disk usage, featuring an AJAX-powered web interface and automatic Telegram alerts for critical temperatures.

---

## 🚀 Features

* **Real-Time Web Dashboard:** Auto-updating interface (via AJAX/Fetch API) without page reloads.
* **Hardware Summary:** Displays OS, Kernel, CPU, and Architecture (similar to `fastfetch`/`neofetch`).
* **System Resources:** Live tracking for CPU, RAM, and all mounted Disks.
* **Temperature Monitoring:** Detailed breakdown of all available thermal sensors.
* **Telegram Alerts:** Automatic notifications sent to your phone if the server exceeds a safe temperature threshold.
* **Minimalist GUI:** A tiny Tkinter window showing the local IP, port, and service status.

---

## 📦 Requirements

* Python 3.12 or higher.
* Required Python libraries:

  * `psutil`
  * `requests`

Install the dependencies using pip:

```bash
pip install psutil requests
```

---

## ⚙️ Configuration

Before running the monitor, open the script and configure your Telegram bot credentials at the top of the file:

```python
# Telegram config
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
TEMP_THRESHOLD = 80.0  # Adjust the critical temperature limit (°C)
```

---

## ▶️ Usage

Since the system is standalone, you only need to run the main script on your server:

```bash
python3 monitor.py
```

> **Note:** If your server does not have a desktop environment (GUI), you may need to disable the Tkinter interface and call `start_server()` and `temperature_monitor()` directly.

---

## 🌐 Accessing the Dashboard

Once running, the script will output your local IP address. Open any web browser on your network and navigate to:

```text
http://<SERVER_IP>:54001
```

---

## 📡 API Endpoint

You can also fetch the raw server data in JSON format for your own custom integrations by making a GET request to:

```text
http://<SERVER_IP>:54001/api/data
```

---


