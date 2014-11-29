import array
import os
import subprocess
import wave

def store(frames, filename):
    with open(filename, mode='w') as out:
        for frame in frames:
            out.write(frame)

    return filename

def decode(filename):
    subprocess.call(['decode', '0', filename, 'decoded_16kHz.pcm', '24000', '7000'])

    wb = wave.open(os.path.splitext(filename)[0] + '_16kHz.wav', mode='w')
    nb = wave.open(os.path.splitext(filename)[0] + '_8kHz.wav', mode='w')
    wb.setparams((1, 2, 16000, 0, 'NONE', 'NOT COMPRESSED'))
    nb.setparams((1, 2, 8000, 0, 'NONE', 'NOT COMPRESSED'))
    with open('decoded_16kHz.pcm', mode='r') as frames:
        raw = frames.read()
        wb.writeframes(raw)
        for i in range(0, len(raw), 2):
            if i % 4 == 0:
                nb.writeframes(raw[i:i + 2])
