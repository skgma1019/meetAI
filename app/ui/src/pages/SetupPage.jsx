import { useState } from 'react'

const QUESTION_TYPES = [
  { id: 'self_intro', label: '자기소개', sub: 'self_intro' },
  { id: 'experience', label: '경험·역량', sub: 'experience' },
  { id: 'motivation', label: '지원 동기', sub: 'motivation' },
]

const DURATIONS = [
  { label: '1분', sec: 60 },
  { label: '3분', sec: 180 },
  { label: '5분', sec: 300 },
]

function RadioItem({ label, sub, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 9,
        border: selected ? '2px solid var(--blue)' : '1.5px solid var(--light-border)',
        borderRadius: 10,
        background: selected ? 'var(--blue-light)' : '#fff',
        padding: '9px 11px',
        cursor: 'pointer',
        width: '100%', textAlign: 'left',
        fontFamily: 'var(--font)',
        transition: 'border-color 0.15s',
      }}
    >
      <span style={{
        width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
        border: selected ? '2px solid var(--blue)' : '1.5px solid var(--light-border)',
        background: selected ? 'radial-gradient(var(--blue) 40%, transparent 45%)' : 'transparent',
      }} />
      <div style={{ flex: 1 }}>
        <span style={{ fontSize: 29, fontWeight: selected ? 700 : 400 }}>{label}</span>
        {sub && <span style={{ fontSize: 23, color: 'var(--muted)', marginLeft: 6 }}>{sub}</span>}
      </div>
    </button>
  )
}

export default function SetupPage({ mode, onNext, onBack }) {
  const [questionType, setQuestionType] = useState('self_intro')
  const [topic, setTopic] = useState('')
  const [durationSec, setDurationSec] = useState(180)
  const [role, setRole] = useState('')
  const [keywords, setKeywords] = useState('')
  const [enableNonverbal, setEnableNonverbal] = useState(false)
  const [nonverbalStyle, setNonverbalStyle] = useState('stable')

  const isInterview = mode === 'interview'
  const modeLabel = isInterview ? '면접' : '발표'

  const handleNext = () => {
    onNext({
      questionType: isInterview ? questionType : null,
      topic: isInterview ? null : topic,
      durationSec,
      role: isInterview ? role : null,
      keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
      enableNonverbal,
      nonverbalStyle,
    })
  }

  return (
    <div className="page-wrap">
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14, minHeight: 580 }}>
          <div className="nav-bar">
            <button className="nav-back" onClick={onBack}>‹</button>
            <span className="chip">{modeLabel}</span>
            <div style={{ width: 30 }} />
          </div>

          {isInterview ? (
            <>
              <div style={{ fontSize: 38, fontWeight: 700 }}>어떤 질문인가요?</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {QUESTION_TYPES.map(q => (
                  <RadioItem
                    key={q.id}
                    label={q.label}
                    sub={q.sub}
                    selected={questionType === q.id}
                    onClick={() => setQuestionType(q.id)}
                  />
                ))}
              </div>
              <div>
                <div style={{ fontSize: 25, color: '#888', marginBottom: 4 }}>지원 직무 (선택)</div>
                <input
                   className="input-field"
                  placeholder="예) backend developer, PM …"
                  value={role}
                  onChange={e => setRole(e.target.value)}
                />
              </div>
              <div>
                <div style={{ fontSize: 25, color: '#888', marginBottom: 4 }}>핵심 키워드 (쉼표 구분, 선택)</div>
                <input
                  className="input-field"
                  placeholder="예) 사용자 분석, 개선, 성과"
                  value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                />
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 38, fontWeight: 700 }}>발표를 설정하세요</div>
              <div>
                <div style={{ fontSize: 25, color: '#888', marginBottom: 4 }}>발표 주제</div>
                <input
                  className="input-field"
                  placeholder="예) 우리 팀의 분기 성과 발표 …"
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                />
              </div>
              <div>
                <div style={{ fontSize: 25, color: '#888', marginBottom: 6 }}>목표 시간</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {DURATIONS.map(d => (
                    <button
                      key={d.sec}
                      className={`pill ${durationSec === d.sec ? 'active' : ''}`}
                      onClick={() => setDurationSec(d.sec)}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 25, color: '#888', marginBottom: 4 }}>핵심 키워드 (쉼표 구분, 선택)</div>
                <input
                  className="input-field"
                  placeholder="예) 성장, 팀워크, 데이터"
                  value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                />
              </div>
            </>
          )}

          {/* Nonverbal settings */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0 6px', borderTop: '1.5px dashed var(--light-border)', marginTop: 8 }}>
            <div>
              <div style={{ fontSize: 29, fontWeight: 700 }}>비언어(몸짓·자세) 분석 포함</div>
              <div style={{ fontSize: 23, color: 'var(--muted)' }}>태도와 제스처도 함께 평가합니다</div>
            </div>
            <div
              className={`toggle ${enableNonverbal ? 'on' : 'off'}`}
              onClick={() => setEnableNonverbal(!enableNonverbal)}
            >
              <div className="toggle-thumb" />
            </div>
          </div>

          {enableNonverbal && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '10px 12px', background: '#faf9f5', border: '1.5px solid var(--light-border)', borderRadius: 10 }}>
              <div style={{ fontSize: 23, color: 'var(--muted)', fontWeight: 700 }}>몸짓 시뮬레이션 스타일</div>
              <div style={{ display: 'flex', gap: 6 }}>
                {[
                  { id: 'stable', label: '차분함' },
                  { id: 'active_hands', label: '큰 제스처' },
                  { id: 'unstable', label: '자세 흔들림' }
                ].map(style => (
                  <button
                    key={style.id}
                    className={`pill ${nonverbalStyle === style.id ? 'active' : ''}`}
                    style={{ flex: 1, padding: '5px 0', fontSize: 23 }}
                    onClick={() => setNonverbalStyle(style.id)}
                  >
                    {style.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          <button className="btn btn-primary" style={{ marginTop: 'auto' }} onClick={handleNext}>
            다음
          </button>
        </div>
      </div>
    </div>
  )
}
