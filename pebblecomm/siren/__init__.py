import array
import os
import subprocess
import wave

def save(params, frames, name):
    with open('encoded.sir7', mode='w') as encoded:
        for frame in frames:
            encoded.write(frame)

    subprocess.check_call(['decode', '0', 'encoded.sir7', 'decoded.pcm', '24000', '7000'])

    if os.path.splitext(name)[1] == '':
        name += '.wav'

    recording = wave.open(name, mode='w')
    recording.setparams(params)
    with open('decoded.pcm', mode='r') as decoded:
        recording.writeframes(decoded.read())
    recording.close()

    return name
