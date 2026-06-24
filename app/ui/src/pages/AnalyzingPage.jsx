import { useState, useEffect } from 'react'

const STEPS = [
  { id: 'stt', label: '음성 전사', sub: 'Whisper STT', delay: 800 },
  { id: 'lang', label: '언어 분석', sub: '간투어·반복·속도·구조 · 룰70%+ML30%', delay: 3000 },
  { id: 'score', label: '통합 점수 계산', sub: '언어 모델 + 베이스라인 혼합', delay: 5500 },
]

export default function AnalyzingPage() {
  const [done, setDone] = useState(new Set())
  const [progress, setProgress] = useState(5)

  useEffect(() => {
    const timers = STEPS.map((s, i) =>
      setTimeout(() => {
        setDone(prev => new Set([...prev, s.id]))
        setProgress(Math.min(95, 20 + i * 35))
      }, s.delay)
    )
    const prog = setInterval(() => setProgress(p => Math.min(p + 1, 90)), 200)
    return () => { timers.forEach(clearTimeout); clearInterval(prog) }
  }, [])

  return (
    <div className="page-wrap" style={{ justifyContent: 'center' }}>
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--muted)', fontFamily: 'var(--font-accent)', fontSize: 27 }}>
            <span>분석</span>
            <span>~10초</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
            <div className="spinner-lg" />
            <div style={{ fontSize: 41, fontWeight: 700 }}>분석하고 있어요…</div>
            <div style={{ fontSize: 23, color: 'var(--muted)', textAlign: 'center', maxWidth: 260 }}>
              처음 실행 시 AI 모델 로딩으로 30초~1분 소요될 수 있습니다
            </div>
          </div>

          {/* Progress bar */}
          <div style={{ height: 13, border: '1.5px solid var(--border)', borderRadius: 8, background: '#eeede6', overflow: 'hidden' }}>
            <div style={{ width: `${progress}%`, height: '100%', background: 'var(--blue)', transition: 'width 0.3s ease', animation: 'progress-fill 0.3s' }} />
          </div>

          {/* Steps */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {STEPS.map(s => {
              const isDone = done.has(s.id)
              const isActive = !isDone && progress > (s.id === 'stt' ? 0 : s.id === 'lang' ? 25 : 60)
              return (
                <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 11, opacity: isDone || isActive ? 1 : 0.45 }}>
                  {isDone ? (
                    <div className="step-icon-done">✓</div>
                  ) : isActive ? (
                    <div className="spinner" style={{ flexShrink: 0 }} />
                  ) : (
                    <div className="step-icon-pending" />
                  )}
                  <div>
                    <div style={{ fontSize: 29, fontWeight: isDone || isActive ? 700 : 400 }}>{s.label}</div>
                    <div style={{ fontSize: 23, color: 'var(--muted)' }}>{s.sub}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
