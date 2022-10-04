#! encoding=utf-8

# Simple MIDI transposer to test the MIDI IN and MIDI OUT.
# Prints all received MIDI Events on the serial console.
# Note On / Note Off will be transposed +12 semitones.
# All other MIDI events are passed through unchanged.

# See: https://docs.micropython.org/en/latest/reference/isr_rules.html
# MicroPython documentation: Writing interrupt handlers

from machine import UART

print("+================================================================+")
print("| MIDI In/Out Test                                               |")
print("+================================================================+")
print("|                                                                |")
print("| UART1 TX (Y9)  = MIDI OUT                                      |")
print("| UART1 RX (Y10) = MID IN                                        |")
print("|                                                                |")
print("| All received MIDI events will be printed on the serial console |")
print("| and sent back through the MIDI OUT. Note On / Note Off will be |")
print("| transposed +12 semitones.                                      |")
print("|                                                                |")
print("+================================================================+")
print("")

buffer = memoryview(bytearray(16))

uart = UART(1)
uart.init(31250, bits=8, parity=None, stop=1)

# Send a test note
uart.writechar(0x90)
uart.writechar(0x40)
uart.writechar(0x64)

machine.lightsleep(2000)

uart.writechar(0x90)
uart.writechar(0x40)
uart.writechar(0x00)

# Raun main loop to echo all MIDI traffic
transpose = 12

while True:
    n = uart.readinto(buffer)
    prev_midi_byte = 0

    if not n:
        continue

    for midi_byte in buffer[:n]:
        # Print original byte on the console
        print(hex(midi_byte))

        # Handle 0x8n = Note Off and 0x9n = Note On
        if prev_midi_byte & 0x80 or prev_midi_byte & 0x90 \
        and midi_byte < 127 - transpose:
            midi_byte += transpose

        prev_midi_byte = midi_byte

        # Echo MIDI byte
        uart.writechar(midi_byte)