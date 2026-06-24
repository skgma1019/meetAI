import React, { useState } from 'react'
import RadarChart from '../components/RadarChart'

export default function ResultPage({ result, mode, setup, onRestart, onExit }) {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('language')

  // Check if this is a Full Analysis (has nonverbal) or Language Only
  const isFullAnalysis = !!result.nonverbal

  // Extract variables based on analysis type
  const finalScore = isFullAnalysis ? result.final_score : (result.language?.overall_score || result.overall_score || 0)
  const summaryText = isFullAnalysis ? result.summary : (result.language?.readable_feedback?.summary || result.readable_feedback?.summary || '')
  
  // Details for language
  const langData = result.language || result
  const langScore = langData.overall_score || 0
  const langMetrics = langData.metrics || []
  const langIssues = langData.detected_issues || []
  
  // Details for nonverbal
  const nonverbalData = result.nonverbal || {}
  const nonverbalScore = nonverbalData.overall_score || 0
  const nonverbalMetrics = nonverbalData.metrics || []
  const nonverbalIssues = nonverbalData.detected_issues || []

  // Combined Feedback (outer for Full, inner language for Language Only)
  const feedback = isFullAnalysis ? result.readable_feedback : langData.readable_feedback || {}
  const strengths = feedback.strengths || []
  const weaknesses = feedback.weaknesses || feedback.improvements || []
  const nextActions = isFullAnalysis ? result.recommendations : (feedback.next_actions || [])

  const improvedAnswer = langData.improved_answer || ''
  const transcript = result.transcript || ''

  const isInterview = mode === 'interview'
  const modeLabel = isInterview ? '면접' : '발표'
  const setupLabel = setup.questionType
    ? { self_intro: '자기소개', experience: '경험·역량', motivation: '지원 동기' }[setup.questionType]
    : (setup.topic || '발표')

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(improvedAnswer)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (e) {
      alert('복사하지 못했습니다.')
    }
  }

  return (
    <div className="page-wrap">
      <div className="screen" style={{ maxWidth: 800 }}>
        {/* Header Navigation */}
        <div className="nav-bar" style={{ marginBottom: 16 }}>
          <button className="nav-back" onClick={onExit} style={{ fontSize: 29, border: '1.5px solid var(--border)', borderRadius: '8px', padding: '4px 10px', background: '#fff', boxShadow: 'var(--shadow-btn)' }}>
            처음으로
          </button>
          <span className="chip" style={{ background: isFullAnalysis ? 'var(--blue)' : 'var(--orange)' }}>
            {modeLabel} · {setupLabel} {isFullAnalysis ? '통합 평가 리포트' : '언어 분석 리포트'}
          </span>
          <div style={{ width: 70 }} />
        </div>

        <div className="result-grid">
          {/* Column 1: Overall Score & Metrics Chart/List */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 36, fontWeight: 700, borderBottom: '2px dashed var(--light-border)', paddingBottom: 8 }}>
              📊 종합 진단
            </div>

            {/* Overall Score Circle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, margin: '8px 0' }}>
              <div style={{
                width: 90, height: 90,
                borderRadius: '24px 20px 26px 18px / 18px 24px 17px 22px',
                border: '2.5px solid var(--border)',
                background: 'var(--stripe-bg)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                boxShadow: 'var(--shadow-card)',
                flexShrink: 0
              }}>
                <span style={{ fontSize: 22, color: 'var(--muted)', fontWeight: 700, lineHeight: 1 }}>{isFullAnalysis ? '최종 점수' : '종합 점수'}</span>
                <span style={{ fontSize: 58, fontWeight: 700, fontFamily: 'var(--font-accent)', color: 'var(--orange)', lineHeight: 1 }}>
                  {Math.round(finalScore)}
                </span>
              </div>
              <div style={{ flex: 1 }}>
                {isFullAnalysis && result.weights && (
                  <div style={{ fontSize: 22, color: 'var(--blue)', fontWeight: 700, marginBottom: 2 }}>
                    반영 가중치: 언어 {Math.round(result.weights.language * 100)}% · 비언어 {Math.round(result.weights.nonverbal * 100)}%
                  </div>
                )}
                <p style={{ fontSize: 27, color: '#333', lineHeight: 1.4, fontWeight: 700 }}>
                  {summaryText || '분석이 성공적으로 완료되었습니다.'}
                </p>
              </div>
            </div>

            {/* If Full Analysis, render Tab selector */}
            {isFullAnalysis && (
              <div style={{ display: 'flex', gap: 6, margin: '6px 0 10px', background: '#faf9f5', border: '1.5px solid var(--light-border)', borderRadius: 12, padding: 3 }}>
                <button
                  className={`pill ${activeTab === 'language' ? 'active' : ''}`}
                  style={{ flex: 1, padding: '5px 0', border: 'none', background: activeTab === 'language' ? 'var(--blue)' : 'transparent', color: activeTab === 'language' ? '#fff' : 'var(--text)', fontWeight: 700, transition: 'all 0.15s' }}
                  onClick={() => setActiveTab('language')}
                >
                  🗣 언어 표현 ({Math.round(langScore)}점)
                </button>
                <button
                  className={`pill ${activeTab === 'nonverbal' ? 'active' : ''}`}
                  style={{ flex: 1, padding: '5px 0', border: 'none', background: activeTab === 'nonverbal' ? 'var(--orange)' : 'transparent', color: activeTab === 'nonverbal' ? '#fff' : 'var(--text)', fontWeight: 700, transition: 'all 0.15s' }}
                  onClick={() => setActiveTab('nonverbal')}
                >
                  🚶 비언어 동작 ({Math.round(nonverbalScore)}점)
                </button>
              </div>
            )}

            {/* Radar Chart & Details depending on active tab or simple language only */}
            {(!isFullAnalysis || activeTab === 'language') ? (
              <>
                <div className="radar-wrap" style={{ margin: '6px auto' }}>
                  <RadarChart metrics={langMetrics} color="#3b6ea5" label="언어 평가 지표" />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  {langMetrics.map(m => {
                    const isGood = m.score >= 70
                    const fillColor = isGood ? 'var(--blue)' : 'var(--orange)'
                    return (
                      <div key={m.name} className="score-bar-row">
                        <span className="score-bar-label" style={{ fontWeight: 700 }}>{m.note || m.name}</span>
                        <div className="score-bar-track">
                          <div
                            className="score-bar-fill"
                            style={{ width: `${m.score}%`, background: fillColor }}
                          />
                        </div>
                        <span className="score-bar-num">{Math.round(m.score)}</span>
                      </div>
                    )
                  })}
                </div>
              </>
            ) : (
              <>
                <div className="radar-wrap" style={{ margin: '6px auto' }}>
                  <RadarChart metrics={nonverbalMetrics} color="#c2683a" label="비언어 평가 지표" />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  {nonverbalMetrics.map(m => {
                    const isGood = m.score >= 70
                    const fillColor = isGood ? 'var(--blue)' : 'var(--orange)'
                    return (
                      <div key={m.name} className="score-bar-row">
                        <span className="score-bar-label" style={{ fontWeight: 700 }}>{m.note || m.name}</span>
                        <div className="score-bar-track">
                          <div
                            className="score-bar-fill"
                            style={{ width: `${m.score}%`, background: fillColor }}
                          />
                        </div>
                        <span className="score-bar-num">{Math.round(m.score)}</span>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>

          {/* Column 2: Strengths & Weaknesses / Tips */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontSize: 36, fontWeight: 700, borderBottom: '2px dashed var(--light-border)', paddingBottom: 8 }}>
              💡 상세 코칭 피드백
            </div>

            {/* Strengths */}
            <div>
              <div style={{ fontSize: 29, fontWeight: 700, color: 'var(--blue)', marginBottom: 6 }}>
                ✓ 이런 점이 좋았어요!
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {strengths.length > 0 ? strengths.map((s, i) => (
                  <div key={i} className="card-inner" style={{ padding: '8px 12px', fontSize: 26, background: 'var(--blue-light)', borderLeft: '3px solid var(--blue)' }}>
                    {s}
                  </div>
                )) : (
                  <div style={{ fontSize: 25, color: 'var(--muted)', paddingLeft: 8 }}>감지된 강점이 없습니다.</div>
                )}
              </div>
            </div>

            {/* Weaknesses */}
            <div>
              <div style={{ fontSize: 29, fontWeight: 700, color: 'var(--orange)', marginBottom: 6 }}>
                ⚠ 이런 점은 아쉬워요…
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {weaknesses.length > 0 ? weaknesses.map((w, i) => (
                  <div key={i} className="card-inner" style={{ padding: '8px 12px', fontSize: 26, background: '#fff9f6', borderLeft: '3px solid var(--orange)' }}>
                    {w}
                  </div>
                )) : (
                  <div style={{ fontSize: 25, color: 'var(--muted)', paddingLeft: 8 }}>특별히 아쉬운 점이 감지되지 않았습니다.</div>
                )}
              </div>
            </div>

            {/* Detected Issues (Filter or combine) */}
            {(!isFullAnalysis || activeTab === 'language') ? (
              langIssues.length > 0 && (
                <div>
                  <div style={{ fontSize: 25, color: '#555', fontWeight: 700, marginBottom: 6 }}>감지된 언어 표현 문제</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {langIssues.map((issue, i) => (
                      <span key={i} className="issue-badge" style={{ fontFamily: 'var(--font)', fontSize: 23, background: '#fff' }}>
                        {issue}
                      </span>
                    ))}
                  </div>
                </div>
              )
            ) : (
              nonverbalIssues.length > 0 && (
                <div>
                  <div style={{ fontSize: 25, color: '#555', fontWeight: 700, marginBottom: 6 }}>감지된 태도/동작 문제</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {nonverbalIssues.map((issue, i) => (
                      <span key={i} className="issue-badge" style={{ fontFamily: 'var(--font)', fontSize: 23, background: '#fff', borderColor: 'var(--orange)', color: 'var(--orange)' }}>
                        {issue}
                      </span>
                    ))}
                  </div>
                </div>
              )
            )}

            {/* Recommended Next Actions */}
            {nextActions.length > 0 && (
              <div style={{ marginTop: 'auto', paddingTop: 10, borderTop: '1.5px dashed var(--light-border)' }}>
                <div style={{ fontSize: 27, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>🎯</span> 다음 말하기 실습을 위한 팁
                </div>
                <ul style={{ paddingLeft: 18, fontSize: 25, lineHeight: 1.5, color: '#444' }}>
                  {nextActions.map((action, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Column 3: Full Width - Transcript & Improved Answer */}
          <div className="card result-full" style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
            <div style={{ fontSize: 36, fontWeight: 700, borderBottom: '2px dashed var(--light-border)', paddingBottom: 8 }}>
              📝 내 답변과 AI 추천 답변 비교
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
              {/* Transcript */}
              <div>
                <div style={{ fontSize: 27, fontWeight: 700, marginBottom: 6, color: '#555' }}>
                  내가 한 답변 내용 (Whisper STT 전사문)
                </div>
                <div className="card-inner" style={{ maxHeight: 180, overflowY: 'auto', fontSize: 26, lineHeight: 1.6, background: '#faf9f5', whiteSpace: 'pre-wrap' }}>
                  {transcript || '녹음이 인식되지 않았습니다.'}
                </div>
              </div>

              {/* Improved Answer */}
              {improvedAnswer && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 27, fontWeight: 700, color: 'var(--blue)' }}>
                      ✨ AI가 제안하는 개선된 답변
                    </span>
                    <button
                      onClick={handleCopy}
                      style={{
                        padding: '3px 8px',
                        fontSize: 22,
                        fontFamily: 'var(--font)',
                        border: '1.5px solid var(--border)',
                        borderRadius: '6px',
                        background: copied ? 'var(--blue)' : '#fff',
                        color: copied ? '#fff' : 'var(--text)',
                        cursor: 'pointer',
                        boxShadow: '1px 1px 0 rgba(0,0,0,0.1)'
                      }}
                    >
                      {copied ? '✓ 복사됨' : '복사하기'}
                    </button>
                  </div>
                  <div className="card-inner" style={{ fontSize: 26, lineHeight: 1.6, background: '#f5f8fc', border: '1.5px dashed var(--blue)', whiteSpace: 'pre-wrap' }}>
                    {improvedAnswer}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div style={{ display: 'flex', gap: 12, marginTop: 14, borderTop: '2px dashed var(--light-border)', paddingTop: 16 }}>
              <button className="btn btn-secondary btn-alt" onClick={onExit} style={{ flex: 1 }}>
                처음 화면으로
              </button>
              <button className="btn btn-primary" onClick={onRestart} style={{ flex: 2 }}>
                다시 연습하기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
