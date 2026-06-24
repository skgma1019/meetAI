import { useState, useRef, useEffect } from 'react'
import { startRecording } from '../utils/wavEncoder'

function fmtTime(sec) {
  const m = String(Math.floor(sec / 60)).padStart(2, '0')
  const s = String(sec % 60).padStart(2, '0')
  return `${m}:${s}`
}

const Waveform = ({ active }) => {
  const bars = [14, 22, 32, 18, 28, 36, 20, 26, 38, 16, 30, 24, 34, 18, 28, 22, 36, 14, 20, 32]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 3, height: 42 }}>
      {bars.map((h, i) => (
        <div
          key={i}
          className={active ? 'waveform-bar' : ''}
          style={{
            width: 4,
            height: active ? h : h * 0.4,
            background: active ? 'var(--blue)' : '#c7c6be',
            borderRadius: 2,
            animationDelay: `${i * 0.04}s`,
            transition: 'height 0.3s',
          }}
        />
      ))}
    </div>
  )
}

export default function RecordPage({ mode, setup, error, onAnalyze, onBack }) {
  const [isRecording, setIsRecording] = useState(false)
  const [duration, setDuration] = useState(0)
  const [audioFile, setAudioFile] = useState(null)
  const [isDrag, setIsDrag] = useState(false)
  const [cameraStream, setCameraStream] = useState(null)
  const [videoBlob, setVideoBlob] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const recRef = useRef(null)
  const videoRecRef = useRef(null)
  const timerRef = useRef(null)
  const fileInputRef = useRef(null)
  const videoRef = useRef(null)

  const modeLabel = mode === 'interview' ? '면접' : '발표'
  const setupLabel = setup.questionType ? { self_intro: '자기소개', experience: '경험·역량', motivation: '지원 동기' }[setup.questionType] : (setup.topic || '발표')
  const targetSec = setup.durationSec || 180

  useEffect(() => {
    return () => {
      clearInterval(timerRef.current)
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop())
      }
    }
  }, [cameraStream])

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl)
    }
  }, [videoUrl])

  useEffect(() => {
    if (videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream
    }
  }, [cameraStream])

  const toggleRecording = async () => {
    if (isRecording) {
      clearInterval(timerRef.current)
      const blob = recRef.current.stop()
      setIsRecording(false)
      setAudioFile(new File([blob], 'recording.wav', { type: 'audio/wav' }))

      // Stop video recording first, then stop camera tracks
      if (videoRecRef.current) {
        const { recorder, chunks } = videoRecRef.current
        recorder.onstop = () => {
          const vBlob = new Blob(chunks, { type: 'video/webm' })
          setVideoBlob(vBlob)
          setVideoUrl(URL.createObjectURL(vBlob))
        }
        recorder.stop()
        videoRecRef.current = null
      }

      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop())
        setCameraStream(null)
      }
    } else {
      try {
        setAudioFile(null)
        setDuration(0)
        setVideoBlob(null)
        setVideoUrl(null)

        if (setup.enableNonverbal) {
          try {
            // Get video+audio combined stream for recording
            const stream = await navigator.mediaDevices.getUserMedia({
              video: { width: 480, height: 300, facingMode: 'user' },
              audio: true,
            })
            setCameraStream(stream)

            const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
              ? 'video/webm;codecs=vp8,opus'
              : 'video/webm'
            const chunks = []
            const recorder = new MediaRecorder(stream, { mimeType })
            recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
            recorder.start()
            videoRecRef.current = { recorder, chunks }
          } catch (camErr) {
            console.warn('카메라를 활성화하지 못했습니다:', camErr)
          }
        }

        recRef.current = await startRecording()
        setIsRecording(true)
        timerRef.current = setInterval(() => setDuration(d => d + 1), 1000)
      } catch (e) {
        alert('마이크 접근 권한이 필요합니다. 브라우저 설정을 확인해주세요.')
      }
    }
  }

  const handleDownloadVideo = () => {
    if (!videoBlob) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(videoBlob)
    a.download = 'recording.webm'
    a.click()
  }

  const handleFileDrop = (e) => {
    e.preventDefault()
    setIsDrag(false)
    const f = e.dataTransfer?.files?.[0] || e.target?.files?.[0]
    if (f) setAudioFile(f)
  }

  const canAnalyze = audioFile && !isRecording


  return (
    <div className="page-wrap">
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="nav-bar">
            <button className="nav-back" onClick={onBack}>‹</button>
            <span className="chip">{modeLabel} · {setupLabel}</span>
            <div style={{ width: 30 }} />
          </div>

          <div style={{ fontSize: 23, fontWeight: 700 }}>녹음하기</div>

          {/* Camera Preview (if nonverbal is enabled) */}
          {setup.enableNonverbal && (
            <div style={{
              width: '100%',
              aspectRatio: '16/10',
              border: '2px solid var(--border)',
              borderRadius: 12,
              background: '#2b2b2b',
              overflow: 'hidden',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {cameraStream ? (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{ width: '100%', height: '100%', objectFit: 'contain', transform: 'scaleX(-1)' }}
                />
              ) : (
                <div style={{ color: '#fff', fontSize: 14, textAlign: 'center', padding: 20 }}>
                  {isRecording ? '카메라를 불러오는 중...' : '녹음 시작 시 카메라가 활성화됩니다.'}
                </div>
              )}

              {/* Overlay simulating active face/body tracking */}
              {isRecording && cameraStream && (
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  border: '2px dashed var(--orange)',
                  borderRadius: 10,
                  pointerEvents: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  animation: 'pulse 1.8s infinite'
                }}>
                  <div style={{
                    color: 'var(--orange)',
                    background: 'rgba(43,43,43,0.85)',
                    padding: '3px 8px',
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 700,
                    position: 'absolute',
                    top: 8,
                    left: 8,
                    fontFamily: 'var(--font)'
                  }}>
                    ● AI 동작 감지 중...
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recorded Video Preview */}
          {videoUrl && !isRecording && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{
                width: '100%',
                aspectRatio: '16/10',
                border: '2px solid var(--border)',
                borderRadius: 12,
                background: '#1a1a1a',
                overflow: 'hidden',
              }}>
                <video
                  src={videoUrl}
                  controls
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>
              <button
                className="btn"
                style={{ border: '1.5px solid var(--border)', background: '#fff', fontSize: 14 }}
                onClick={handleDownloadVideo}
              >
                ↓ 영상 다운로드 (recording.webm)
              </button>
            </div>
          )}

          {/* Mic recorder */}
          <div className="card-inner" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div style={{ position: 'relative', width: 92, height: 92, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {isRecording && <div className="pulse-ring" />}
              <button
                onClick={toggleRecording}
                style={{
                  position: 'relative',
                  width: 80, height: 80, borderRadius: '50%',
                  border: '2.5px solid var(--border)',
                  background: '#fff',
                  boxShadow: '3px 3px 0 rgba(43,43,43,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                <div style={{
                  width: isRecording ? 28 : 44,
                  height: isRecording ? 28 : 44,
                  borderRadius: isRecording ? 4 : '50%',
                  background: 'var(--orange)',
                  transition: 'all 0.2s',
                }} />
              </button>
            </div>

            <div style={{ fontFamily: 'var(--font-accent)', fontSize: 28, lineHeight: 1 }}>
              {fmtTime(duration)}{' '}
              <span style={{ fontSize: 17, color: 'var(--muted)' }}>/ 목표 {fmtTime(targetSec)}</span>
            </div>

            <Waveform active={isRecording} />

            <div style={{ fontSize: 13, color: isRecording ? 'var(--orange)' : 'var(--muted)' }}>
              {isRecording ? '● 녹음 중 — 또박또박 말해보세요' : audioFile ? `✓ ${audioFile.name}` : '● 버튼을 눌러 녹음 시작'}
            </div>
          </div>

          {/* divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--muted)', fontSize: 13 }}>
            <span style={{ flex: 1, borderTop: '1.5px dashed var(--light-border)' }} />
            또는
            <span style={{ flex: 1, borderTop: '1.5px dashed var(--light-border)' }} />
          </div>

          {/* File upload */}
          <div
            className={`upload-area ${isDrag ? 'drag-over' : ''} ${audioFile ? 'has-file' : ''}`}
            onDragOver={e => { e.preventDefault(); setIsDrag(true) }}
            onDragLeave={() => setIsDrag(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp3,.wav,.m4a,.ogg,.flac,.webm,.mp4"
              style={{ display: 'none' }}
              onChange={handleFileDrop}
            />
            {audioFile && !isRecording ? (
              <>
                <div style={{ fontSize: 15, color: 'var(--blue)', fontWeight: 700 }}>✓ {audioFile.name}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>다른 파일 선택하려면 클릭</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 15, color: '#777' }}>미디어 파일 끌어다 놓기</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>mp3 · wav · mp4 · m4a · webm</div>
              </>
            )}
          </div>

          {error && (
            <div style={{ background: '#fff3f0', border: '1.5px solid var(--orange)', borderRadius: 8, padding: '10px 12px', fontSize: 14, color: 'var(--orange)' }}>
              ⚠ {error}
            </div>
          )}

          <button
            className="btn btn-primary"
            style={{ opacity: canAnalyze ? 1 : 0.5 }}
            disabled={!canAnalyze}
            onClick={() => onAnalyze(audioFile, videoBlob)}
          >
            분석 시작
          </button>
        </div>
      </div>
    </div>
  )
}
