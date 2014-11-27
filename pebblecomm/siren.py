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

  out = wave.open(os.path.splitext(filename)[0] + '_16kHz.wav', mode='w')
  out.setparams((1, 2, 16000, 0, 'NONE', 'NOT COMPRESSED'))
  with open('decoded_16kHz.pcm', mode='r') as frames:
    out.writeframes(frames.read())
