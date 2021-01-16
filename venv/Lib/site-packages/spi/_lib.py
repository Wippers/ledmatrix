# -*- coding: utf-8 -*-

from fcntl import ioctl
import struct
import ctypes


# generic IOCTL stuff
IO = 0
IOW = 1
IOR = 2
SPI_IOC_MAGIC = ord('k')
SPI_IOC_WR_MODE = 1


def _IOC(typ, nr, size, direction):
    """ generic IOCTL structure """
    # 32bit: 2 bit direction, 14 bit size, 8bit type 8 bit nr,
    # r = ((size | (direction << 14)) << 16) | cmd
    r = direction << 30 | size << 16 | typ << 8 | nr
    return r


def _SPI_IOC_MESSAGE(size):
    """ size is the number of transfers """
    return _IOC(SPI_IOC_MAGIC, 0, 32 * size, IOR)  # should be IOW


def spi_transfer(txbuf=None, readlen=None, speedhz=0):
    """ prepares the data for a transfer part

        a single transfer can be either read, write or both
        concatenate more transfers to begin read/write at different times

        txbuf: bytes to send (if any)
        readlen: bytes to read
        if both parameters are present, len(txbuf) == readlen !
    """
    if txbuf is None:
        _txpointer = 0
        writelen = 0
        wbuf = None
    else:
        wbuf = ctypes.create_string_buffer(txbuf)
        _txpointer = ctypes.addressof(wbuf)
        writelen = len(txbuf)
    if txbuf and readlen and len(txbuf) != readlen:
        raise(ValueError("unaligned access"))
    if readlen is not None and readlen > 0:
        rbuf = ctypes.create_string_buffer(readlen)
        _rxpointer = ctypes.addressof(rbuf)
    else:
        _rxpointer = 0
        rbuf = None
    oplen = readlen or writelen
    delay_usec = 0
    bits_per_word = 0
    cs_change = 0
    pad = 0
    return struct.pack("QQLLHBBL",  #64 64 32 32 16 8 8 32 b = 32B
                _txpointer,
                _rxpointer,
                oplen,
                speedhz,
                delay_usec,
                bits_per_word,
                cs_change,
                pad
                ), wbuf, rbuf



class SPIDev(object):
    def __init__(self, device, spimode=0):
        self._file = open(device, 'r+')
        self._no = self._file.fileno()
        param = _IOC(SPI_IOC_MAGIC, SPI_IOC_WR_MODE, 1, IOW)
        assert spimode in range(4)
        value = ctypes.c_int8(spimode)  # SPI MODE 0
        ioctl(self._no, param, ctypes.addressof(value))

    def do_transfers(self, transfers):
        megabuf = ctypes.create_string_buffer("".join(transfers))
        param = _SPI_IOC_MESSAGE(len(transfers))
        p = megabuf
        ioctl(self._no, param, p)

