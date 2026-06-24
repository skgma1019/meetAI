function writeStr(view, offset, s) {
  for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i))
}

export function encodeWAV(pcm, sampleRate) {
  const buf = new ArrayBuffer(44 + pcm.length * 2)
  const v = new DataView(buf)
  writeStr(v, 0, 'RIFF')
  v.setUint32(4, 36 + pcm.length * 2, true)
  writeStr(v, 8, 'WAVE')
  writeStr(v, 12, 'fmt ')
  v.setUint32(16, 16, true)
  v.setUint16(20, 1, true)
  v.setUint16(22, 1, true)
  v.setUint32(24, sampleRate, true)
  v.setUint32(28, sampleRate * 2, true)
  v.setUint16(32, 2, true)
  v.setUint16(34, 16, true)
  writeStr(v, 36, 'data')
  v.setUint32(40, pcm.length * 2, true)
  let off = 44
  for (let i = 0; i < pcm.length; i++) {
    const s = Math.max(-1, Math.min(1, pcm[i]))
    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    off += 2
  }
  return new Blob([buf], { type: 'audio/wav' })
}

export async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } })
  const ctx = new AudioContext()
  const src = ctx.createMediaStreamSource(stream)
  const proc = ctx.createScriptProcessor(4096, 1, 1)
  const chunks = []

  proc.onaudioprocess = (e) => {
    chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)))
  }
  src.connect(proc)
  proc.connect(ctx.destination)

  return {
    stop() {
      proc.disconnect()
      src.disconnect()
      stream.getTracks().forEach((t) => t.stop())
      const sr = ctx.sampleRate
      ctx.close()
      const total = chunks.reduce((a, c) => a + c.length, 0)
      const merged = new Float32Array(total)
      let off = 0
      for (const c of chunks) { merged.set(c, off); off += c.length }
      return encodeWAV(merged, sr)
    },
  }
}
