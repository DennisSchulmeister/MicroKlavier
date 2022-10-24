#! encoding=utf-8

# Simple MIDI transposer to test the MIDI IN and MIDI OUT.
# Prints all received MIDI Events on the serial console.
# Note On / Note Off will be echoed as chords.
# All other MIDI events are passed through unchanged.

# See: https://docs.micropython.org/en/latest/reference/isr_rules.html
# MicroPython documentation: Writing interrupt handlers

import machine
from machine import UART

hex_map = {0: "0x00",  1: "0x01",  2: "0x02",  3: "0x03",  4: "0x04",  5: "0x05",  6: "0x06",  7: "0x07",
           8: "0x08",  9: "0x09", 10: "0x0a", 11: "0x0b", 12: "0x0c", 13: "0x0d", 14: "0x0e", 15: "0x0f"}

@micropython.viper
def hex2(value: int):
    if value < 16:
        return hex_map[value]
    else:
        return hex(value)

@micropython.viper
def run() -> int:
    print("+===============================================================+")
    print("| MIDI In/Out Test                                              |")
    print("+===============================================================+")
    print("|                                                               |")
    print("| UART1 TX (Y9)  = MIDI OUT                                     |")
    print("| UART1 RX (Y10) = MID IN                                       |")
    print("|                                                               |")
    print("| All received MIDI events will be sent back through MIDI OUT.  |")
    print("| Note On / Note Off will be played back as major chords        |")
    print("|                                                               |")
    print("+===============================================================+")
    print("")

    uart: UART = UART(1)
    uart.init(31250, bits=8, parity=None, stop=1)

    # Send some test notes
    uart.writechar(0x90)
    uart.writechar(0x40)
    uart.writechar(0x64)

    uart.writechar(0x90)
    uart.writechar(0x44)
    uart.writechar(0x64)

    uart.writechar(0x90)
    uart.writechar(0x47)
    uart.writechar(0x64)

    machine.lightsleep(250)

    uart.writechar(0x90)
    uart.writechar(0x40)
    uart.writechar(0x00)

    uart.writechar(0x90)
    uart.writechar(0x44)
    uart.writechar(0x00)

    uart.writechar(0x90)
    uart.writechar(0x47)
    uart.writechar(0x00)

    # Echo MIDI messages, but playback Note On/Off as major chords
    note_message = ptr8(bytearray(3))
    index = 0
    play_note = False
    first_seen = False
    chord_transpose = [0, 4, 7]

    while True:
        midi_byte = int(uart.readchar())

        if midi_byte < 0 or midi_byte == 0xfe or midi_byte == 0xfc:
            continue

        # Print received bytes on the console
        if midi_byte > 127:
            print()
        if midi_byte <= 127 and index == 1 and not first_seen:
            # Log running status
            print("\n    ", end=" ")
        print(hex2(midi_byte), end=" ")

        # Capture note events and echo all other bytes
        if (midi_byte & 0xF0 == 0x80) or (midi_byte & 0xF0 == 0x90):
            # Note On (0x8n) or Note Off (0x9n)
            note_message[0] = midi_byte
            note_message[1] = 0x00
            note_message[2] = 0x00

            index = 1
            first_seen = True
            continue
        elif midi_byte > 127:
            # Other MIDI message
            index = 0

        if index > 0:
            note_message[index] = midi_byte
            index += 1

            if index > 2:
                # For now assume, the next byte will be the
                # first data byte of the same message type
                index = 1
                play_note = True
                first_seen = False
        else:
            uart.writechar(midi_byte)

        # Play modified notes, once a full note message has been captures
        if play_note:
            print("  >> PLAY: ", end=" ")
            play_note = False

            for offset in chord_transpose:
                for i in range(3):
                    midi_byte = note_message[i]

                    if i == 1 and midi_byte <= 127 - int(offset):
                        midi_byte += int(offset)

                    uart.writechar(midi_byte)
                    print(hex2(midi_byte), end=" ")
                
                print("", end=" ")