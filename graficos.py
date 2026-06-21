#!/usr/bin/env python3
"""
ESP-NOW Receiver - Visualizador em tempo real e registrador de dados
Lê dados da Serial do ESP32, plota 4 gráficos em tempo real e salva em CSV.
"""

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import csv
import re
import threading
import os
from datetime import datetime

# ─── Configurações ─────────────────────────────────────────────────────────
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
ROLLING_WINDOW_S = 30
PLOT_INTERVAL_MS = 20
CSV_DIR = 'dados'

# ─── Regex para parsear linha Serial ──────────────────────────────────────
# Formato: "1.234s  LC1:   12.3g  LC2:   45.6g  TC1:  25.4C  TC2:  26.1C"
PATTERN = re.compile(
    r'(\d+\.\d+)s\s+LC1:\s*([-\d.]+)g\s+LC2:\s*([-\d.]+)g\s+'
    r'TC1:\s*([-\d.]+)C\s+TC2:\s*([-\d.]+)C'
)

# ─── Buffers thread-safe ──────────────────────────────────────────────────
lock = threading.Lock()
time_buf = deque()
lc1_buf = deque()
lc2_buf = deque()
tc1_buf = deque()
tc2_buf = deque()

running = True


def serial_reader():
    """Thread: lê Serial, parseia, armazena e salva CSV."""
    global running

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    except serial.SerialException as e:
        print(f"[ERRO] Não foi possível abrir {SERIAL_PORT}: {e}")
        running = False
        return

    os.makedirs(CSV_DIR, exist_ok=True)
    fname = datetime.now().strftime(f'{CSV_DIR}/dados_%Y-%m-%d_%H-%M-%S.csv')
    f_csv = open(fname, 'w', newline='')
    writer = csv.writer(f_csv)
    writer.writerow(['timestamp_s', 'load_cell_1_g', 'load_cell_2_g',
                     'thermocouple_1_c', 'thermocouple_2_c'])
    f_csv.flush()

    print(f"[OK] Conectado a {SERIAL_PORT} @ {BAUD_RATE} baud")
    print(f"[OK] Salvando dados em {fname}")

    while running:
        try:
            raw = ser.readline()
        except serial.SerialException:
            print("[ERRO] Conexão serial perdida.")
            break

        try:
            line = raw.decode('utf-8', errors='replace').strip()
        except Exception:
            continue
        if not line:
            continue

        m = PATTERN.search(line)
        if not m:
            continue

        t = float(m.group(1))
        l1 = float(m.group(2))
        l2 = float(m.group(3))
        t1 = float(m.group(4))
        t2 = float(m.group(5))

        with lock:
            time_buf.append(t)
            lc1_buf.append(l1)
            lc2_buf.append(l2)
            tc1_buf.append(t1)
            tc2_buf.append(t2)

            while time_buf and time_buf[-1] - time_buf[0] > ROLLING_WINDOW_S:
                time_buf.popleft()
                lc1_buf.popleft()
                lc2_buf.popleft()
                tc1_buf.popleft()
                tc2_buf.popleft()

        writer.writerow([t, l1, l2, t1, t2])
        f_csv.flush()

    ser.close()
    f_csv.close()
    print("[OK] CSV salvo.")
    running = False


# ─── Gráficos ──────────────────────────────────────────────────────────────
fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True, constrained_layout=True)
fig.suptitle('ESP-NOW \u2013 Dados em Tempo Real', fontsize=14, fontweight='bold')

cores = ['#2196F3', '#F44336', '#4CAF50', '#9C27B0']
linhas = []
ylabel = ['Load Cell 1 (g)', 'Load Cell 2 (g)',
          'Termopar 1 (°C)', 'Termopar 2 (°C)']
bufs = [lc1_buf, lc2_buf, tc1_buf, tc2_buf]

for ax, c, yl in zip(axes, cores, ylabel):
    line, = ax.plot([], [], c=c, linewidth=1.2)
    linhas.append(line)
    ax.set_ylabel(yl)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel('Tempo (s)')


def init():
    for line in linhas:
        line.set_data([], [])
    return linhas


def animate(frame):
    with lock:
        if not time_buf:
            return linhas
        t = list(time_buf)
        dados = [list(lc1_buf), list(lc2_buf), list(tc1_buf), list(tc2_buf)]

    if len(t) < 2:
        return linhas

    for line, d in zip(linhas, dados):
        line.set_data(t, d)

    xpad = max(1.0, (t[-1] - t[0]) * 0.05)
    axes[-1].set_xlim(t[0] - xpad, t[-1] + xpad)

    for ax, d in zip(axes, dados):
        if d:
            ymin, ymax = min(d), max(d)
            if ymin == ymax:
                ypad = 1.0
            else:
                ypad = (ymax - ymin) * 0.1
            ax.set_ylim(ymin - ypad, ymax + ypad)

    return linhas


ani = animation.FuncAnimation(
    fig, animate, init_func=init, interval=PLOT_INTERVAL_MS,
    blit=False, cache_frame_data=False
)

# ─── Loop principal ────────────────────────────────────────────────────────
thread_serial = threading.Thread(target=serial_reader, daemon=True)
thread_serial.start()

try:
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    running = False
    thread_serial.join(timeout=2)
    print("[OK] Programa encerrado.")
