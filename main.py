#!/usr/bin/env python3

import subprocess
import threading
import serial
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

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
            ser = serial.Serial(
                SERIAL_PORT,
                BAUDRATE,
                timeout=0.2
            )

            # Arduino reset nach USB-Verbindung abwarten
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


def serial_to_mc():
    global ser

    while True:

        if ser is None or not ser.is_open:
            connect_serial()

        try:
            data = ser.readline()

            if data:
                command = data.decode(
                    errors="ignore"
                ).strip()

                if command:
                    print("Arduino >", command)
                    send_to_minecraft(command)

        except Exception as e:
            print("Serial Fehler:", e)

            try:
                ser.close()
            except:
                pass

            ser = None


def mc_output():
    while True:
        line = server.stdout.readline()

        if not line:
            break

        print("MC:", line, end="")


threading.Thread(
    target=serial_to_mc,
    daemon=True
).start()

threading.Thread(
    target=mc_output,
    daemon=True
).start()


server.wait()