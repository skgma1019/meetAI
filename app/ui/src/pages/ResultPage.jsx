import React, { useState } from 'react'
import RadarChart from '../components/RadarChart'

export default function ResultPage({ result, mode, setup, onRestart, onExit }) {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('language')

  const isFullAnalysis = !!result.nonverbal

  // Pronunciation & Gemini AI
  const pronunciationScore100 = result.pronunciation_score_100
  const pronunciationGrade = result.pronunciation_grade
  const geminiData = result.gemini_feedback

  // Score extraction
  const finalScore = result.final_score != null
    ? result.final_score
    : (isFullAnalysis ? result.final_score : (result.language?.overall_score || result.overall_score || 0))
  const summaryText = geminiData?.overall_comment
    || (isFullAnalysis ? result.summary : (result.language?.readable_feedback?.summary || result.readable_feedback?.summary || ''))

  const langData = result.language || result
  const langScore = langData.overall_score || 0
  const langMetrics = langData.metrics || []
  const langIssues = langData.detected_issues || []

  const nonverbalData = result.nonverbal || {}
  const nonverbalScoreVal = nonverbalData.overall_score ?? result.nonverbal_score ?? null
  const nonverbalScore = nonverbalScoreVal || 0
  const nonverbalMetrics = nonverbalData.metrics || []
  const nonverbalIssues = nonverbalData.detected_issues || []

  const feedback = geminiData
    ? { strengths: geminiData.strengths || [], weaknesses: geminiData.improvements || [] }
    : (isFullAnalysis ? result.readable_feedback : langData.readable_feedback || {})
  const strengths = feedback.strengths || []
  const weaknesses = feedback.weaknesses || feedback.improvements || []
  const nextActions = geminiData
    ? []
    : (isFullAnalysis ? result.recommendations : (feedback.next_actions || []))

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
    } catch {
      alert('복사하지 못했습니다.')
    }
  }

  // SVG ring: r=52, circumference ≈ 327
  const ringFill = Math.round((Math.min(100, Math.max(0, finalScore)) / 100) * 327)

  const activeMetrics = (!isFullAnalysis || activeTab === 'language') ? langMetrics : nonverbalMetrics
  const activeIssues  = (!isFullAnalysis || activeTab === 'language') ? langIssues  : nonverbalIssues

  return (
    <div className="page-wrap">
      <div className="screen" style={{ maxWidth: 860 }}>

        {/* ── 헤더 ─────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, paddingBottom: 16, borderBottom: '1.5px dashed var(--light-border)', marginBottom: 20,
        }}>
          <button
            onClick={onExit}
            style={{ fontSize: 20, border: '1.5px solid var(--border)', borderRadius: '10px 8px 11px 7px / 7px 11px 8px 10px', padding: '6px 14px', background: '#fff', boxShadow: 'var(--shadow-btn)', cursor: 'pointer', whiteSpace: 'nowrap', fontFamily: 'var(--font)' }}
          >
            ‹ 처음으로
          </button>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1.2, flex: 1 }}>
            <div style={{ fontSize: 26, fontWeight: 700 }}>{modeLabel} · {setupLabel} 평가 리포트</div>
            <div style={{ fontFamily: 'var(--font-accent)', fontSize: 18, color: 'var(--blue)' }}>meetAI coaching report</div>
          </div>
          <div style={{ border: '1.5px solid var(--border)', borderRadius: 20, padding: '6px 14px', fontSize: 15, background: '#fbfbf7', whiteSpace: 'nowrap' }}>
            {modeLabel} · {setupLabel}
          </div>
        </div>

        {/* ── Hero: 종합 점수 링 + 3 메트릭 카드 ──────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, marginBottom: 20 }}>

          {/* 종합 점수 원형 게이지 */}
          <div className="card" style={{ borderRadius: '16px 12px 17px 11px / 11px 16px 10px 15px', padding: 22, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{ fontSize: 13, letterSpacing: 2, color: 'var(--muted)', fontWeight: 700 }}>종합 점수</div>
            <div style={{ position: 'relative', width: 160, height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="160" height="160" viewBox="0 0 120 120" style={{ position: 'absolute', top: 0, left: 0, transform: 'rotate(-90deg)' }}>
                <circle cx="60" cy="60" r="52" fill="none" stroke="#eeede6" strokeWidth="11" />
                <circle cx="60" cy="60" r="52" fill="none" stroke="var(--blue)" strokeWidth="11" strokeLinecap="round" strokeDasharray={`${ringFill} 327`} />
              </svg>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-accent)', fontSize: 60, fontWeight: 700, lineHeight: 0.85, color: '#2b2b2b' }}>
                  {Math.round(finalScore)}
                </div>
                <div style={{ fontSize: 13, color: 'var(--muted)' }}>/ 100점</div>
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-accent)', fontSize: 18, color: 'var(--blue)', textAlign: 'center', lineHeight: 1.3 }}>
              {summaryText || '분석이 완료되었습니다!'}
            </div>
            {result.weights && (
              <div style={{ marginTop: 4, fontSize: 13, color: 'var(--muted)', textAlign: 'center', borderTop: '1.5px dashed var(--light-border)', paddingTop: 8, width: '100%' }}>
                반영 가중치 · 언어 {Math.round(result.weights.language * 100)}%
                {result.weights.nonverbal != null && ` + 비언어 ${Math.round(result.weights.nonverbal * 100)}%`}
                {result.weights.pronunciation != null && ` + 발음 ${Math.round(result.weights.pronunciation * 100)}%`}
              </div>
            )}
          </div>

          {/* 3 메트릭 카드 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, alignContent: 'stretch' }}>

            {/* 언어 표현 */}
            <div style={{ border: '1.5px solid var(--border)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fff', boxShadow: 'var(--shadow-card)', padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, fontWeight: 700 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--blue)', flexShrink: 0 }} />
                언어 표현
              </div>
              <div style={{ fontFamily: 'var(--font-accent)', fontSize: 44, fontWeight: 700, lineHeight: 0.85 }}>{langScore.toFixed(1)}</div>
              <div style={{ height: 10, background: '#eeede6', border: '1.5px solid var(--border)', borderRadius: 6, overflow: 'hidden', marginTop: 'auto' }}>
                <div style={{ width: `${langScore}%`, height: '100%', background: 'var(--blue)' }} />
              </div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>간투어·속도·구조 종합</div>
            </div>

            {/* 비언어 동작 */}
            <div style={{ border: '1.5px solid var(--border)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fff', boxShadow: 'var(--shadow-card)', padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, fontWeight: 700 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: nonverbalScoreVal != null ? 'var(--blue)' : '#b6b5ab', flexShrink: 0 }} />
                비언어 동작
              </div>
              <div style={{ fontFamily: 'var(--font-accent)', fontSize: 44, fontWeight: 700, lineHeight: 0.85, color: nonverbalScoreVal != null ? '#2b2b2b' : 'var(--muted)' }}>
                {nonverbalScoreVal != null ? nonverbalScore.toFixed(1) : '—'}
              </div>
              <div style={{ height: 10, background: '#eeede6', border: '1.5px solid var(--border)', borderRadius: 6, overflow: 'hidden', marginTop: 'auto' }}>
                <div style={{ width: `${nonverbalScore}%`, height: '100%', background: nonverbalScoreVal != null ? 'var(--blue)' : 'transparent' }} />
              </div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>자세·손동작·머리동작</div>
            </div>

            {/* 발음 명료도 */}
            <div style={{ border: '1.5px solid var(--border)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fff', boxShadow: 'var(--shadow-card)', padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, fontWeight: 700 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: pronunciationScore100 != null ? 'var(--blue)' : '#b6b5ab', flexShrink: 0 }} />
                발음 명료도
              </div>
              <div style={{ fontFamily: 'var(--font-accent)', fontSize: 44, fontWeight: 700, lineHeight: 0.85, color: pronunciationScore100 != null ? '#2b2b2b' : 'var(--muted)' }}>
                {pronunciationScore100 != null ? Math.round(pronunciationScore100) : '—'}
              </div>
              <div style={{ height: 10, background: '#eeede6', border: '1.5px solid var(--border)', borderRadius: 6, overflow: 'hidden', marginTop: 'auto' }}>
                <div style={{ width: `${pronunciationScore100 || 0}%`, height: '100%', background: 'var(--blue)' }} />
              </div>
              <div style={{ fontSize: 13, color: pronunciationScore100 != null ? 'var(--blue)' : 'var(--muted)' }}>
                {pronunciationGrade ? `등급 · ${pronunciationGrade}` : '음성 파일 분석 시 표시'}
              </div>
            </div>

          </div>
        </div>

        {/* ── 중단: 세부 진단 + 코칭 피드백 ──────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.05fr 1fr', gap: 20, marginBottom: 20, alignItems: 'start' }}>

          {/* 세부 진단 카드 */}
          <div className="card" style={{ borderRadius: '15px 12px 16px 11px / 11px 16px 10px 15px', padding: 22 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 20, fontWeight: 700, marginBottom: 14 }}>
              <span style={{ width: 24, height: 24, borderRadius: 6, background: 'var(--blue)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>
              </span>
              {(!isFullAnalysis || activeTab === 'language') ? '언어 표현 세부 진단' : '비언어 동작 세부 진단'}
            </div>

            {/* 탭 선택 (Full Analysis 전용) */}
            {isFullAnalysis && (
              <div style={{ display: 'flex', gap: 6, marginBottom: 14, background: '#faf9f5', border: '1.5px solid var(--light-border)', borderRadius: 12, padding: 3 }}>
                <button
                  style={{ flex: 1, padding: '5px 0', border: 'none', borderRadius: 9, background: activeTab === 'language' ? 'var(--blue)' : 'transparent', color: activeTab === 'language' ? '#fff' : 'var(--text)', fontWeight: 700, fontFamily: 'var(--font)', cursor: 'pointer', fontSize: 16 }}
                  onClick={() => setActiveTab('language')}
                >
                  🗣 언어 ({Math.round(langScore)}점)
                </button>
                <button
                  style={{ flex: 1, padding: '5px 0', border: 'none', borderRadius: 9, background: activeTab === 'nonverbal' ? 'var(--orange)' : 'transparent', color: activeTab === 'nonverbal' ? '#fff' : 'var(--text)', fontWeight: 700, fontFamily: 'var(--font)', cursor: 'pointer', fontSize: 16 }}
                  onClick={() => setActiveTab('nonverbal')}
                >
                  🚶 비언어 ({Math.round(nonverbalScore)}점)
                </button>
              </div>
            )}

            {/* 레이더 차트 */}
            <div className="radar-wrap" style={{ margin: '0 auto 10px' }}>
              <RadarChart
                metrics={activeMetrics}
                color={(!isFullAnalysis || activeTab === 'language') ? '#3b6ea5' : '#c2683a'}
                label={(!isFullAnalysis || activeTab === 'language') ? '언어 평가 지표' : '비언어 평가 지표'}
              />
            </div>

            {/* 점수 바 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {activeMetrics.map(m => (
                <div key={m.name} style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
                  <div style={{ width: 140, fontSize: 15, color: '#444' }}>{m.note || m.name}</div>
                  <div style={{ flex: 1, height: 13, background: '#eeede6', border: '1.5px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                    <div style={{ width: `${m.score}%`, height: '100%', background: m.score >= 70 ? 'var(--blue)' : 'var(--orange)' }} />
                  </div>
                  <div style={{ width: 32, textAlign: 'right', fontFamily: 'var(--font-accent)', fontSize: 22, fontWeight: 700 }}>{Math.round(m.score)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 코칭 피드백 카드 */}
          <div className="card" style={{ borderRadius: '12px 15px 11px 16px / 16px 11px 15px 10px', padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 20, fontWeight: 700 }}>
              💡 상세 코칭 피드백
            </div>

            {/* 잘한 점 (초록) */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 17, fontWeight: 700, color: '#1f8a5b', marginBottom: 8 }}>
                ✓ 이런 점이 좋았어요
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {strengths.length > 0 ? strengths.map((s, i) => (
                  <div key={i} style={{ border: '1.5px solid var(--border)', borderLeft: '4px solid #1f8a5b', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fbfbf7', padding: '9px 12px', fontSize: 16, color: '#3a3a3a', lineHeight: 1.45 }}>
                    {s}
                  </div>
                )) : (
                  <div style={{ fontSize: 15, color: 'var(--muted)', paddingLeft: 8 }}>감지된 강점이 없습니다.</div>
                )}
              </div>
            </div>

            {/* 아쉬운 점 (주황) */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 17, fontWeight: 700, color: 'var(--orange)', marginBottom: 8 }}>
                ⚠ 이런 점은 아쉬워요
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {weaknesses.length > 0 ? weaknesses.map((w, i) => (
                  <div key={i} style={{ border: '1.5px solid var(--border)', borderLeft: '4px solid var(--orange)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fbfbf7', padding: '9px 12px', fontSize: 16, color: '#3a3a3a', lineHeight: 1.45 }}>
                    {w}
                  </div>
                )) : (
                  <div style={{ fontSize: 15, color: 'var(--muted)', paddingLeft: 8 }}>특별히 아쉬운 점이 없습니다.</div>
                )}
              </div>
            </div>

            {/* 감지된 문제 뱃지 */}
            {activeIssues.length > 0 && (
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#6b6b6b', marginBottom: 8 }}>
                  감지된 {(!isFullAnalysis || activeTab === 'language') ? '언어 표현' : '태도/동작'} 문제
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {activeIssues.map((issue, i) => (
                    <span key={i} style={{ border: '1.5px solid var(--orange)', color: 'var(--orange)', borderRadius: 18, padding: '4px 13px', fontSize: 14 }}>
                      {issue}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Gemini 상세 피드백 (영상 분석 시) */}
            {geminiData?.language_feedback && (
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--blue)', marginBottom: 6 }}>🗣 언어 표현 피드백</div>
                <div style={{ border: '1.5px solid var(--border)', borderLeft: '3px solid var(--blue)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#f5f8fc', padding: '9px 12px', fontSize: 15, lineHeight: 1.6 }}>
                  {geminiData.language_feedback}
                </div>
              </div>
            )}
            {geminiData?.nonverbal_feedback && (
              <div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--orange)', marginBottom: 6 }}>🚶 비언어 표현 피드백</div>
                <div style={{ border: '1.5px solid var(--border)', borderLeft: '3px solid var(--orange)', borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px', background: '#fff9f6', padding: '9px 12px', fontSize: 15, lineHeight: 1.6 }}>
                  {geminiData.nonverbal_feedback}
                </div>
              </div>
            )}

            {/* 다음 실습 팁 */}
            {nextActions.length > 0 && (
              <div style={{ marginTop: 'auto', borderTop: '1.5px dashed var(--light-border)', paddingTop: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 16, fontWeight: 700, color: 'var(--blue)', marginBottom: 8 }}>
                  🎯 다음 실습을 위한 팁
                </div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 15, color: '#444', lineHeight: 1.55 }}>
                  {nextActions.map((action, i) => (
                    <li key={i}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

        </div>

        {/* ── 답변 비교: 2컬럼 좌우 나란히 ───────────────────── */}
        <div className="card" style={{ borderRadius: '14px 12px 15px 11px / 11px 15px 10px 14px', padding: 22, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
            📝 내 답변 vs AI 추천 답변
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* 내 답변 */}
            <div>
              <div style={{ fontSize: 15, color: '#888', marginBottom: 7 }}>내가 한 답변 · Whisper STT 전사문</div>
              <div style={{ border: '1.5px solid #e3e2da', borderRadius: 10, background: '#faf9f5', padding: 14, fontSize: 15, color: '#4a4a4a', lineHeight: 1.65, height: 200, overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                {transcript || '녹음이 인식되지 않았습니다.'}
              </div>
            </div>
            {/* AI 개선 답변 */}
            {improvedAnswer ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 15, fontWeight: 700, color: 'var(--blue)' }}>
                    ✨ AI가 제안하는 개선된 답변
                  </div>
                  <button
                    onClick={handleCopy}
                    style={{ border: '1.5px solid var(--border)', borderRadius: 8, background: copied ? 'var(--blue)' : '#fff', color: copied ? '#fff' : 'var(--text)', padding: '4px 11px', fontSize: 14, fontFamily: 'var(--font)', cursor: 'pointer', boxShadow: '2px 2px 0 rgba(43,43,43,0.1)' }}
                  >
                    {copied ? '✓ 복사됨' : '복사하기'}
                  </button>
                </div>
                <div style={{ border: '1.5px solid var(--blue)', borderLeft: '5px solid var(--blue)', borderRadius: 10, background: '#f2f6fb', padding: 14, fontSize: 15, color: '#2f3f52', lineHeight: 1.65, height: 200, overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                  {improvedAnswer}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1.5px dashed var(--light-border)', borderRadius: 10, background: '#faf9f5', color: 'var(--muted)', fontSize: 15, minHeight: 200 }}>
                AI 개선 답변이 없습니다.
              </div>
            )}
          </div>
        </div>

        {/* ── Footer CTA ──────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 14 }}>
          <button className="btn btn-secondary btn-alt" onClick={onExit} style={{ flex: 1 }}>
            처음 화면으로
          </button>
          <button className="btn btn-primary" onClick={onRestart} style={{ flex: 2 }}>
            다시 연습하기 ↺
          </button>
        </div>

      </div>
    </div>
  )
}
