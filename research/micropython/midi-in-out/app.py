#! encoding=utf-8

# Simple MIDI transposer to test the MIDI IN and MIDI OUT.
# Prints all received MIDI Events on the serial console.
# Note On / Note Off will be transposed +12 semitones.
# All other MIDI events are passed through unchanged.

# See: https://docs.micropython.org/en/latest/reference/isr_rules.html
# MicroPython documentation: Writing interrupt handlers
import machine, micropython
from machine import UART
from typing import Tuple

micropython.alloc_emergency_exception_buf(100)

class InterruptProducerBuffer:
    """
    A simple byte buffer to collect data produced by an interrupt handler.
    Only one consumer (usually the main loop) is supported. The main loop
    can get a copy of all waiting data at any time, as long as the buffer
    is large enough to not overrun.
    
    One large, pre-allocated memory region is used and split into three
    distinctive areas that will be reused throughout the lifetime of the
    buffer. No new objects will be created except in the constructor to
    prevent memory fragmentation and often garbage collection runs. This
    is because Python objects live on the heap and even seemingly innocent
    operations like slicing a `memoryview` create new objects on the heap.

    As a downside, all received data will usually be copied two times between
    the different memory regions. But since an interrupt usually only generates
    a few bytes (e.g. at most eight bytes for UART), this is neglectable.
    """

    def __init__(self, isr_buffer=8, latency=3) -> None:
        """
        Constructor. This is the only method where objects are created on the
        heap to reserve memory for the buffer. For this one large `bytearray`
        with several `memoryview`s on it are created.

        Parameters:

         * `isr_buffer`: The maximum number of bytes that can be read during
           an interrupt. e.g. the documentation of the `UART` class states,
           that an interrupt is triggered for no more than eight bytes. A single
           memory region of exactly this size is allocated for the ISR handler.
        
         * `latency`: The number of interrupts that can occur before an buffer
           overrun happens in worst cases. Memory of `isr_buffer * latency`
           bytes is allocated to collect all waiting data. A separate memory
           area of the same size as allocated to actually pass the data to the
           main loop.
           
        Note that the total memory usage is `(latency * 2 + 1) * isr_buffer` bytes
        plus the object instances itself.
        """
        size  = (latency * 2 + 1) * isr_buffer
        split = (0, isr_buffer, isr_buffer * (latency + 1))

        self._memory_all  = memoryview(bytearray(size))
        self._memory_isr  = self._memory_all[split[0]:split[1]]
        self._memory_wait = self._memory_all[split[1]:split[2]]
        self._memory_data = self._memory_all[split[2]:]

        self._overrun = False
        self._waiting = 0

    @property
    def memory_isr(self) -> memoryview:
        """
        Get the memory region into which the ISR can place new data.
        """
        return self._memory_isr
    
    def commit(self, length: int) -> None:
        """
        To be called in the ISR after new data has been placed in `memory_isr`.
        This appends the data to a separate internal memory region called the
        waiting area from which the main loop can retrieve it later.

        Parameters:

         * `length`: Number of bytes placed in `memory_isr`
        """
        memory_isr  = self._memory_isr
        memory_wait = self._memory_wait
        waiting_old = self._waiting
        waiting_new = waiting_old + length

        if waiting_new > len(memory_wait):
            self._overrun = True
            return
        
        i = 0
        while i < length:
            memory_wait[waiting_old + i] = memory_isr[i]
            i += 1

        self._waiting = waiting_new

    @property
    def data(self) -> Tuple[memoryview, int]:
        """
        To be called in the main loop to retrieve all waiting data since the
        last call. This copies the data from the waiting area to yet another
        memory region that can be freely used by the caller.

        Note, that the returned memory region will always be the same to prevent
        memory fragmentation due to excessive object creation on the heap. Above
        all, no new `memoryview` instance will be created but the same instance
        returned together with the amount of retrieved data. The remainder of the
        memory region will contain old data from previous calls that must be ignored.

        This method also "empties" the waiting area, allowing the buffer to place
        new data there. It is therefor crucial to periodically call this method
        in order to prevent buffer overruns. Once an overrun occurs all new data
        will be discarded until this method is called.

        Note, that this method temporarily disables interrupt handling to prevent
        memory corruption.

        If possible at all, callers should avoid using splice syntax to read
        the new data. Rather use direct index access in a loop to prevent
        creation of lots of derived short-lived `memoryview`s on the heap.

        Returns:

         * `memoryivew` to access the data
         * Number of read bytes
        """
        irq_state = machine.disable_irq()
        
        memory_wait = self._memory_wait
        memory_data = self._memory_data
        waiting     = self._waiting

        i = 0
        while i < waiting:
            memory_data[i] = memory_wait[i]
            i += 1

        self._waiting = 0
        self._overrun = False

        machine.enable_irq(irq_state)

        return memory_data, waiting
    
    @property
    def overrun(self) -> bool:
        """
        Flag indicating the loss of data because the main task didn't retrieve
        it fast enough. Will be cleared the next time `data` is called.
        """
        return self._overrun

class MIDIHandler:
    """
    Handling of all MIDI input and output.
    """

    def __init__(self, uart: int, print_events: bool = True) -> None:
        """
        Initialize MIDI handling on the given UART number.
        """
        self._buffer = InterruptProducerBuffer(isr_buffer=8, latency=3)
        
        self._uart = UART(uart)
        self._uart.init(31250, bits=8, parity=None, stop=1)
        self._uart.irq(UART.RX_ANY, handler=self._on_uart_interrupt)

        self._print_events = print_events

    def _on_uart_interrupt(self) -> None:
        """
        Interrupt handler called by the underlying UART object when there
        are between one and eight bytes available.
        """
        buffer = self._buffer
        length = self._uart.readinto(buffer.memory_isr)
        buffer.commit(length)

    def process(self):
        """
        To be called in the main-loop to process all received MIDI events.
        """
        uart = self._uart
        midi_bytes, length = self._buffer.data

        i = 0
        while i < length:
            # TODO: Real MIDI handling
            midi_byte = midi_bytes[i]
            uart.writechar(midi_byte)
            print(hex(midi_byte))
            i += 1

def run():
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

    midi1 = MIDIHandler(uart=1, print_events=True)

    while True:
        midi1.process()