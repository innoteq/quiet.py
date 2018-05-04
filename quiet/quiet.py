

import time
import os
import json
from ctypes import *
from numpy.ctypeslib import ndpointer
import numpy


c_float_p = POINTER(c_float)


class Quiet(object):
    def __init__(self, sample_rate=44100.0, profiles="/usr/local/share/quiet/quiet-profiles.json", profile_name='ultrasonic-experimental'):
        self._load_lib()

        self._encoder_options = self._lib.quiet_encoder_profile_filename(profiles, profile_name)
        self._encoder = self._lib.quiet_encoder_create(self._encoder_options, sample_rate)

        self._decoder_options = self._lib.quiet_decoder_profile_filename(profiles, profile_name)
        self._decoder = self._lib.quiet_decoder_create(self._decoder_options, sample_rate)
        # self._lib.quiet_decoder_set_nonblocking(self._decoder)

    def __del__(self):
        self._lib.quiet_encoder_destroy(self._encoder)
        self._lib.quiet_decoder_destroy(self._decoder)

    def decode(self, data, flush=False):
        self._lib.quiet_decoder_consume(self._decoder, data.ctypes.data_as(c_void_p), len(data))

        if flush:
            self._lib.quiet_decoder_flush(self._decoder)

        buf = numpy.empty(128, dtype='uint8')
        got = self._lib.quiet_decoder_recv(self._decoder, buf, len(buf))
        
        if got > 0:
            return buf[:got]

    def flush(self):
        self._lib.quiet_decoder_flush(self._decoder)

        code = []
        while True:
            buf = numpy.empty(128, dtype='uint8')
            got = self._lib.quiet_decoder_recv(self._decoder, buf, len(buf))
            
            if got <= 0:
                 break

            code.append(buf[:got].tostring())

    def encode(self, buf):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def _load_lib(self):
        lib_name = 'libquiet.so'
        lib_path = os.path.join(os.path.dirname(__file__), lib_name)

        self._lib = cdll.LoadLibrary(lib_path)

        # quiet_encoder_options *quiet_encoder_profile_filename(const char *fname, const char *profilename)
        self._lib.quiet_encoder_profile_filename.argtypes = [c_char_p, c_char_p]
        self._lib.quiet_encoder_profile_filename.restype = c_void_p

        # quiet_decoder_options *quiet_decoder_profile_filename(const char *fname, const char *profilename)
        self._lib.quiet_decoder_profile_filename.argtypes = [c_char_p, c_char_p]
        self._lib.quiet_decoder_profile_filename.restype = c_void_p

        # quiet_encoder *quiet_encoder_create(const quiet_encoder_options *opt, float sample_rate)
        self._lib.quiet_encoder_create.argtypes = [c_void_p, c_float]
        self._lib.quiet_encoder_create.restype = c_void_p

        # ssize_t quiet_encoder_send(quiet_encoder *e, const void *buf, size_t len)
        self._lib.quiet_encoder_send.argtypes = [c_void_p, c_void_p, c_int]
        self._lib.quiet_encoder_send.restype = c_int

        # void quiet_encoder_set_blocking(quiet_encoder *e, time_t sec, long nano)
        # self._lib.quiet_encoder_set_blocking.argtypes = [c_void_p, c_uint, c_long]
        # self._lib.quiet_encoder_set_blocking.restype = c_int

        # void quiet_encoder_set_nonblocking(quiet_encoder *e)

        # size_t quiet_encoder_clamp_frame_len(quiet_encoder *e, size_t sample_len)
        self._lib.quiet_encoder_clamp_frame_len.argtypes = [c_void_p, c_uint]
        self._lib.quiet_encoder_clamp_frame_len.restype = c_uint

        # size_t quiet_encoder_get_frame_len(const quiet_encoder *e)
        self._lib.quiet_encoder_get_frame_len.argtypes = [c_void_p]
        self._lib.quiet_encoder_get_frame_len.restype = c_uint

        # ssize_t quiet_encoder_emit(quiet_encoder *e, quiet_sample_t *samplebuf, size_t samplebuf_len)
        self._lib.quiet_encoder_emit.argtypes = [c_void_p, ndpointer(c_float, flags="C_CONTIGUOUS"), c_size_t]
        self._lib.quiet_encoder_emit.restype = c_ssize_t

        # void quiet_encoder_close(quiet_encoder *e)
        self._lib.quiet_encoder_close.argtypes = [c_void_p]
        self._lib.quiet_encoder_close.restype = None

        # void quiet_encoder_destroy(quiet_encoder *e)
        self._lib.quiet_encoder_destroy.argtypes = [c_void_p]
        self._lib.quiet_encoder_destroy.restype = None


        # quiet_decoder *quiet_decoder_create(const quiet_decoder_options *opt, float sample_rate)
        self._lib.quiet_decoder_create.argtypes = [c_void_p, c_float]
        self._lib.quiet_decoder_create.restype = c_void_p

        # ssize_t quiet_decoder_recv(quiet_decoder *d, uint8_t *data, size_t len)
        self._lib.quiet_decoder_recv.argtypes = [c_void_p, ndpointer(c_uint8, flags="C_CONTIGUOUS"), c_size_t]
        self._lib.quiet_decoder_recv.restype = c_ssize_t

        # void quiet_decoder_set_nonblocking(quiet_decoder *d)
        self._lib.quiet_decoder_set_nonblocking.argtypes = [c_void_p]
        self._lib.quiet_decoder_set_nonblocking.restype = None

        # void quiet_decoder_consume(quiet_decoder *d, const quiet_sample_t *samplebuf, size_t sample_len)
        self._lib.quiet_decoder_consume.argtypes = [c_void_p, c_void_p, c_size_t]
        self._lib.quiet_decoder_consume.restype = None

        # bool quiet_decoder_frame_in_progress(quiet_decoder *d)

        # void quiet_decoder_flush(quiet_decoder *d)
        self._lib.quiet_decoder_flush.argtypes = [c_void_p]
        self._lib.quiet_decoder_flush.restype = None

        # void quiet_decoder_close(quiet_decoder *d)
        self._lib.quiet_decoder_close.argtypes = [c_void_p]
        self._lib.quiet_decoder_close.restype = None

        # unsigned int quiet_decoder_checksum_fails(const quiet_decoder *d)
        self._lib.quiet_decoder_checksum_fails.argtypes = [c_void_p]
        self._lib.quiet_decoder_checksum_fails.restype = c_uint

        # void quiet_decoder_enable_stats(quiet_decoder *d)

        # void quiet_decoder_disable_stats(quiet_decoder *d)

        # void quiet_decoder_set_stats_blocking(quiet_decoder *d, time_t sec, long nano)

        # void quiet_decoder_set_stats_nonblocking(quiet_decoder *d)

        # void quiet_decoder_destroy(quiet_decoder *d)
        self._lib.quiet_decoder_destroy.argtypes = [c_void_p]
        self._lib.quiet_decoder_destroy.restype = None


def main():
    import pyaudio
    import audioop
    import Queue

    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 44100
    CHUNK = 16384  # int(RATE / 100)

    t = Quiet()

    p = pyaudio.PyAudio()
    q = Queue.Queue()

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
    with Quiet(profile_name='ultrasonic-experimental') as quiet:
        while True:
            try:
                audio = q.get()
                audio = numpy.fromstring(audio, dtype='float32')
                # audio = audio[::CHANNELS]
                code = quiet.decode(audio)
                if code is not None:
                    count += 1
                    print(count, code.tostring())
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    main()
