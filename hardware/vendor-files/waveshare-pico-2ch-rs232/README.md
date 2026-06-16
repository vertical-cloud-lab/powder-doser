# Waveshare Pico-2CH-RS232 (vendor files)

2-channel RS-232 module for the Raspberry Pi Pico (SP3232EEN transceiver,
UART↔RS232). Used on the powder-doser control board to talk to the A&D
HR-100A balance over RS-232 **without** populating a discrete MAX3232 +
its ~5 charge-pump capacitors on our own board — those parts are already
embedded on this module (see the schematic datasheet below).

* Product / wiki: <https://www.waveshare.com/wiki/Pico-2CH-RS232>
* Operating voltage 3.3–5 V, baud 300–912600 bps, 21.00 × 52.00 mm.

## Pico interface (from `datasheets/Pico_2CH_RS232_SchDoc.pdf`)

| Module | Pico | Description |
| --- | --- | --- |
| VCC  | VSYS | Power input |
| GND  | GND  | Ground |
| TXD0 | GP0  | Channel 0 UART transmit (Pico TX) |
| RXD0 | GP1  | Channel 0 UART receive (Pico RX) |
| TXD1 | GP4  | Channel 1 UART transmit (Pico TX) |
| RXD1 | GP5  | Channel 1 UART receive (Pico RX) |

On the powder-doser starter board the module mounts on a **side 2×20 header**
(in the spirit of Adafruit's Proto Doubler PiCowbell, #5906) next to the Pico W,
and the four UART lines are routed by board copper to *free* Pico UART pins
(GP12/GP13 for channel 0 = scale, GP8/GP9 for channel 1 = spare) so they do not
collide with the I²C (GP0/GP1) and Tic stepper UART (GP4/GP5) already in use.

## Datasheets

| File | Source |
| --- | --- |
| `datasheets/Pico_2CH_RS232_SchDoc.pdf` | Waveshare module schematic (PR #76 discussion) |
| `datasheets/SP3232EEN.pdf` | MaxLinear/Sipex SP3232E RS-232 transceiver datasheet |
