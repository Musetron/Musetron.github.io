#!/usr/bin/env python3

import subprocess
import threading
import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

# Lock für thread-sicheres Schreiben auf die serielle Schnittstelle
serial_lock = threading.Lock()

server = subprocess.Popen(
    [
        "java",
        "-Xms1G",
        "-Xmx2G",
        "-jar",
        "server.jar",
        "nogui"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

ser = None


def connect_serial():
    global ser

    while True:
        try:
            with serial_lock:
                ser = serial.Serial(
                    SERIAL_PORT,
                    BAUDRATE,
                    timeout=0.2
                )
            
            # Arduino Reset nach USB-Verbindung abwarten
            time.sleep(2)

            print(f"Verbunden mit {SERIAL_PORT}")
            return

        except Exception as e:
            print("Warte auf serielles Gerät...", e)
            time.sleep(2)


def send_to_minecraft(command):
    try:
        print("MC <", command)
        server.stdin.write(command + "\n")
        server.stdin.flush()
    except Exception as e:
        print("Minecraft stdin Fehler:", e)


def send_to_arduino(message):
    """ Sendet Antworten von Minecraft sicher zurück an den Arduino """
    global ser
    with serial_lock:
        if ser and ser.is_open:
            try:
                # Zeilenumbruch anfügen, damit der Arduino readStringUntil('\n') nutzen kann
                ser.write((message + "\n").encode('utf-8'))
            except Exception as e:
                print("Fehler beim Senden an Arduino:", e)


def serial_to_mc():
    global ser

    while True:
        if ser is None or not ser.is_open:
            connect_serial()

        try:
            data = None
            with serial_lock:
                if ser and ser.is_open:
                    data = ser.readline()

            if data:
                command = data.decode(errors="ignore").strip()
                if command:
                    print("Arduino >", command)
                    send_to_minecraft(command)

        except Exception as e:
            print("Serial Fehler:", e)
            with serial_lock:
                if ser:
                    try:
                        ser.close()
                    except:
                        pass
                    ser = None


def mc_output():
    """ Liest den Minecraft-Output und leitet ihn an den Arduino weiter """
    while True:
        line = server.stdout.readline()

        if not line:
            break

        line_clean = line.strip()
        print("MC:", line_clean)

        # Echo-Schutz: Verhindert, dass Konsolen-Logs des Servers als 
        # neue Befehle missverstanden werden oder Endlosschleifen erzeugen.
        # Falls du NUR bestimmte Antworten senden willst, kannst du hier filtern.
        if line_clean:
            send_to_arduino(line_clean)


# Threads starten
threading.Thread(target=serial_to_mc, daemon=True).start()
threading.Thread(target=mc_output, daemon=True).start()

server.wait()
