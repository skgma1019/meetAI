import { useState, useEffect } from 'react'
import { getAccessToken, getVideoSignedUrl } from '../supabase'

function ScoreCircle({ score }) {
  const s = Math.round(score ?? 0)
  const color = s >= 80 ? 'var(--blue)' : s >= 60 ? 'var(--orange)' : '#c44'
  return (
    <div style={{
      width: 52, height: 52, borderRadius: '50%',
      border: `3px solid ${color}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <span style={{ fontSize: 27, fontWeight: 700, color, fontFamily: 'var(--font-accent)' }}>{s}</span>
    </div>
  )
}

function fmtDate(iso) {
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export default function HistoryPage({ onBack, onViewResult }) {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [detailId, setDetailId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [videoUrl, setVideoUrl] = useState(null)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    fetchList()
  }, [])

  const fetchList = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = await getAccessToken()
      const res = await fetch('/history', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(`${res.status}`)
      setRecords(await res.json())
    } catch (e) {
      setError('기록을 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const openDetail = async (id) => {
    setDetailId(id)
    setDetailLoading(true)
    setVideoUrl(null)
    try {
      const token = await getAccessToken()
      const res = await fetch(`/history/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setDetail(data)
      if (data.video_path) {
        const url = await getVideoSignedUrl(data.video_path)
        setVideoUrl(url)
      }
    } catch {
      setDetail(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const closeDetail = () => {
    setDetailId(null)
    setDetail(null)
    setVideoUrl(null)
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!window.confirm('이 기록을 삭제할까요?')) return
    setDeleting(id)
    const token = await getAccessToken()
    await fetch(`/history/${id}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    setDeleting(null)
    setRecords(prev => prev.filter(r => r.id !== id))
    if (detailId === id) closeDetail()
  }

  const modeLabel = m => m === 'interview' ? '면접' : '발표'

  if (detailId) {
    return (
      <div className="page-wrap">
        <div className="screen">
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="nav-bar">
              <button className="nav-back" onClick={closeDetail}>‹</button>
              <span style={{ fontWeight: 700, fontSize: 29 }}>분석 상세</span>
              <div style={{ width: 30 }} />
            </div>

            {detailLoading && (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)' }}>불러오는 중…</div>
            )}

            {!detailLoading && detail && (
              <>
                {/* 영상 미리보기 */}
                {videoUrl && (
                  <div style={{ border: '2px solid var(--border)', borderRadius: 12, overflow: 'hidden', background: '#1a1a1a' }}>
                    <video src={videoUrl} controls style={{ width: '100%', maxHeight: 220, objectFit: 'contain' }} />
                  </div>
                )}

                {/* 기본 정보 */}
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="chip">{modeLabel(detail.mode)}</span>
                  <span style={{ fontSize: 23, color: 'var(--muted)' }}>{fmtDate(detail.created_at)}</span>
                  <ScoreCircle score={detail.overall_score} />
                </div>

                {/* 전사문 */}
                {detail.transcript && (
                  <div className="card-inner" style={{ fontSize: 23, color: '#444', lineHeight: 1.7, maxHeight: 120, overflowY: 'auto' }}>
                    {detail.transcript}
                  </div>
                )}

                {/* 개선 답변 */}
                {detail.improved_answer && (
                  <div>
                    <div style={{ fontSize: 23, fontWeight: 700, marginBottom: 6, color: 'var(--blue)' }}>AI 개선 답변</div>
                    <div className="card-inner" style={{ fontSize: 23, color: '#444', lineHeight: 1.7, maxHeight: 120, overflowY: 'auto' }}>
                      {detail.improved_answer}
                    </div>
                  </div>
                )}

                {/* 결과 페이지로 이동 */}
                {detail.feedback && (
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      const result = {
                        ...detail.feedback,
                        transcript: detail.transcript,
                      }
                      onViewResult(result, detail.mode)
                    }}
                  >
                    상세 결과 보기
                  </button>
                )}

                <button
                  className="btn"
                  style={{ border: '1.5px solid #e88', color: '#c44', background: '#fff' }}
                  onClick={(e) => handleDelete(detail.id, e)}
                >
                  기록 삭제
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page-wrap">
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="nav-bar">
            <button className="nav-back" onClick={onBack}>‹</button>
            <span style={{ fontWeight: 700, fontSize: 29 }}>분석 기록</span>
            <div style={{ width: 30 }} />
          </div>

          {loading && (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div className="spinner-lg" />
            </div>
          )}

          {error && (
            <div style={{ background: '#fff3f0', border: '1.5px solid var(--orange)', borderRadius: 8, padding: '10px 12px', fontSize: 25, color: 'var(--orange)' }}>
              {error}
            </div>
          )}

          {!loading && records.length === 0 && !error && (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted)' }}>
              <div style={{ fontSize: 58, marginBottom: 8 }}>📂</div>
              <div>아직 분석 기록이 없어요.</div>
              <div style={{ fontSize: 23, marginTop: 4 }}>녹음하고 분석해보세요!</div>
            </div>
          )}

          {!loading && records.map(r => (
            <div
              key={r.id}
              onClick={() => openDetail(r.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                border: '1.5px solid var(--border)',
                borderRadius: 12,
                padding: '12px 14px',
                cursor: 'pointer',
                background: '#faf9f4',
                transition: 'box-shadow 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.boxShadow = '2px 2px 0 rgba(43,43,43,0.12)'}
              onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
            >
              <ScoreCircle score={r.overall_score} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <span className="chip" style={{ fontSize: 20, padding: '1px 7px' }}>{modeLabel(r.mode)}</span>
                  {r.video_path && <span style={{ fontSize: 20, color: 'var(--blue)' }}>● 영상</span>}
                </div>
                <div style={{ fontSize: 22, color: 'var(--muted)' }}>{fmtDate(r.created_at)}</div>
              </div>
              <button
                onClick={(e) => handleDelete(r.id, e)}
                disabled={deleting === r.id}
                style={{ background: 'none', border: 'none', color: '#ccc', cursor: 'pointer', fontSize: 32, padding: '4px 6px' }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
