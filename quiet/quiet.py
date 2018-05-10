

import time
import os
import json
from ctypes import c_char_p, c_void_p, c_float, c_size_t, c_ssize_t, c_uint, c_uint8, POINTER, cdll
from numpy.ctypeslib import ndpointer
import numpy


PROFILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quiet-profiles.json')

c_float_p = POINTER(c_float)


class Quiet(object):
    # for lazy loading
    lib = None

    @staticmethod
    def load_lib():
        lib_name = 'libquiet.so'
        lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), lib_name)

        if os.path.isfile(lib_path):
            lib = cdll.LoadLibrary(lib_path)
        else:
            lib = cdll.LoadLibrary(lib_name)

        # quiet_encoder_options *quiet_encoder_profile_filename(const char *fname, const char *profilename)
        lib.quiet_encoder_profile_filename.argtypes = [c_char_p, c_char_p]
        lib.quiet_encoder_profile_filename.restype = c_void_p

        # quiet_decoder_options *quiet_decoder_profile_filename(const char *fname, const char *profilename)
        lib.quiet_decoder_profile_filename.argtypes = [c_char_p, c_char_p]
        lib.quiet_decoder_profile_filename.restype = c_void_p

        # quiet_encoder *quiet_encoder_create(const quiet_encoder_options *opt, float sample_rate)
        lib.quiet_encoder_create.argtypes = [c_void_p, c_float]
        lib.quiet_encoder_create.restype = c_void_p

        # ssize_t quiet_encoder_send(quiet_encoder *e, const void *buf, size_t len)
        lib.quiet_encoder_send.argtypes = [c_void_p, c_char_p, c_size_t]
        lib.quiet_encoder_send.restype = c_ssize_t

        # void quiet_encoder_set_blocking(quiet_encoder *e, time_t sec, long nano)
        # lib.quiet_encoder_set_blocking.argtypes = [c_void_p, c_uint, c_long]
        # lib.quiet_encoder_set_blocking.restype = None

        # void quiet_encoder_set_nonblocking(quiet_encoder *e)

        # size_t quiet_encoder_clamp_frame_len(quiet_encoder *e, size_t sample_len)
        lib.quiet_encoder_clamp_frame_len.argtypes = [c_void_p, c_size_t]
        lib.quiet_encoder_clamp_frame_len.restype = c_size_t

        # size_t quiet_encoder_get_frame_len(const quiet_encoder *e)
        lib.quiet_encoder_get_frame_len.argtypes = [c_void_p]
        lib.quiet_encoder_get_frame_len.restype = c_size_t

        # ssize_t quiet_encoder_emit(quiet_encoder *e, quiet_sample_t *samplebuf, size_t samplebuf_len)
        lib.quiet_encoder_emit.argtypes = [
            c_void_p, ndpointer(c_float, flags="C_CONTIGUOUS"), c_size_t]
        lib.quiet_encoder_emit.restype = c_ssize_t

        # void quiet_encoder_close(quiet_encoder *e)
        lib.quiet_encoder_close.argtypes = [c_void_p]
        lib.quiet_encoder_close.restype = None

        # void quiet_encoder_destroy(quiet_encoder *e)
        lib.quiet_encoder_destroy.argtypes = [c_void_p]
        lib.quiet_encoder_destroy.restype = None

        # quiet_decoder *quiet_decoder_create(const quiet_decoder_options *opt, float sample_rate)
        lib.quiet_decoder_create.argtypes = [c_void_p, c_float]
        lib.quiet_decoder_create.restype = c_void_p

        # ssize_t quiet_decoder_recv(quiet_decoder *d, uint8_t *data, size_t len)
        lib.quiet_decoder_recv.argtypes = [
            c_void_p, ndpointer(c_uint8, flags="C_CONTIGUOUS"), c_size_t]
        lib.quiet_decoder_recv.restype = c_ssize_t

        # void quiet_decoder_set_nonblocking(quiet_decoder *d)
        # lib.quiet_decoder_set_nonblocking.argtypes = [c_void_p]
        # lib.quiet_decoder_set_nonblocking.restype = None

        # void quiet_decoder_consume(quiet_decoder *d, const quiet_sample_t *samplebuf, size_t sample_len)
        lib.quiet_decoder_consume.argtypes = [c_void_p, c_void_p, c_size_t]
        lib.quiet_decoder_consume.restype = None

        # bool quiet_decoder_frame_in_progress(quiet_decoder *d)

        # void quiet_decoder_flush(quiet_decoder *d)
        lib.quiet_decoder_flush.argtypes = [c_void_p]
        lib.quiet_decoder_flush.restype = None

        # void quiet_decoder_close(quiet_decoder *d)
        lib.quiet_decoder_close.argtypes = [c_void_p]
        lib.quiet_decoder_close.restype = None

        # unsigned int quiet_decoder_checksum_fails(const quiet_decoder *d)
        lib.quiet_decoder_checksum_fails.argtypes = [c_void_p]
        lib.quiet_decoder_checksum_fails.restype = c_uint

        # void quiet_decoder_enable_stats(quiet_decoder *d)

        # void quiet_decoder_disable_stats(quiet_decoder *d)

        # void quiet_decoder_set_stats_blocking(quiet_decoder *d, time_t sec, long nano)

        # void quiet_decoder_set_stats_nonblocking(quiet_decoder *d)

        # void quiet_decoder_destroy(quiet_decoder *d)
        lib.quiet_decoder_destroy.argtypes = [c_void_p]
        lib.quiet_decoder_destroy.restype = None

        return lib


class Decoder(object):
    def __init__(self, sample_rate=44100., profile_name='audible', profiles=PROFILES, max_frame=128):
        if not Quiet.lib:
            Quiet.lib = Quiet.load_lib()

        self._decoder_options = Quiet.lib.quiet_decoder_profile_filename(
            profiles.encode('utf-8'), profile_name.encode('utf-8'))
        self._decoder = Quiet.lib.quiet_decoder_create(
            self._decoder_options, sample_rate)

        self.max_frame = max_frame

    def __del__(self):
        Quiet.lib.quiet_decoder_destroy(self._decoder)

    def decode(self, data, flush=False):
        Quiet.lib.quiet_decoder_consume(
            self._decoder, data.ctypes.data_as(c_void_p), len(data))

        if flush:
            Quiet.lib.quiet_decoder_flush(self._decoder)

        buf = numpy.empty(self.max_frame, dtype='uint8')
        got = Quiet.lib.quiet_decoder_recv(self._decoder, buf, len(buf))

        if got > 0:
            return buf[:got]

    def flush(self):
        Quiet.lib.quiet_decoder_flush(self._decoder)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


class Encoder(object):
    def __init__(self, sample_rate=44100., profile_name='audible', profiles=PROFILES):
        if not Quiet.lib:
            Quiet.lib = Quiet.load_lib()

        self._encoder_options = Quiet.lib.quiet_encoder_profile_filename(
            profiles.encode('utf-8'), profile_name.encode('utf-8'))
        self._encoder = Quiet.lib.quiet_encoder_create(
            self._encoder_options, sample_rate)

    def __del__(self):
        Quiet.lib.quiet_encoder_destroy(self._encoder)

    def encode(self, data, chunk_size=1024):
        Quiet.lib.quiet_encoder_send(
            self._encoder, data.encode('utf-8'), len(data))

        buf = numpy.empty(chunk_size, dtype='float32')
        while True:
            got = Quiet.lib.quiet_encoder_emit(self._encoder, buf, len(buf))

            if got < 0:
                return
            elif got < chunk_size:
                yield buf
                return
            else:
                yield buf

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


def decode():
    import pyaudio
    import sys
    if sys.version_info[0] < 3:
        import Queue as queue
    else:
        import queue

    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 44100
    CHUNK = 16384  # int(RATE / 100)

    p = pyaudio.PyAudio()
    q = queue.Queue()

    def callback(in_data, frame_count, time_info, status):
        q.put(in_data)
        return (None, pyaudio.paContinue)

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    count = 0
    with Decoder(profile_name='ultrasonic-experimental') as decoder:
        while True:
            try:
                audio = q.get()
                audio = numpy.fromstring(audio, dtype='float32')
                # audio = audio[::CHANNELS]
                code = decoder.decode(audio)
                if code is not None:
                    count += 1
                    print(code.tostring().decode('utf-8', 'ignore'))
            except KeyboardInterrupt:
                break


def test():
    encoder = Encoder()
    decoder = Decoder()

    for chunk in encoder.encode('hello, world'):
        message = decoder.decode(chunk)
        if message is not None:
            print(message)


if __name__ == '__main__':
    decode()
