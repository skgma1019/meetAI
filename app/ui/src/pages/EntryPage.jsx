const MicIcon = () => (
  <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="2.5" width="6" height="11" rx="3"/>
    <path d="M6 11a6 6 0 0 0 12 0"/>
    <line x1="12" y1="17" x2="12" y2="21"/>
    <line x1="8.5" y1="21" x2="15.5" y2="21"/>
  </svg>
)

export default function EntryPage({ onStart }) {
  return (
    <div className="page-wrap">
      <div className="screen">
        <div className="card" style={{ minHeight: 540, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', color: '#b6b5ab', fontFamily: 'var(--font-accent)', fontSize: 15 }}>
            <span style={{ display: 'flex', gap: 3 }}>
              {[0,1,2].map(i => <span key={i} style={{ width: 5, height: 5, borderRadius: '50%', background: '#b6b5ab', display: 'inline-block' }} />)}
            </span>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18, textAlign: 'center' }}>
            <div style={{
              width: 96, height: 96,
              border: '2px solid var(--border)',
              borderRadius: '26px 20px 28px 18px / 18px 26px 17px 26px',
              background: '#fff',
              boxShadow: '4px 4px 0 rgba(43,43,43,0.12)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <MicIcon />
            </div>

            <div>
              <div style={{ fontSize: 44, fontWeight: 700, lineHeight: 1 }}>면보아</div>
              <div style={{ fontFamily: 'var(--font-accent)', fontSize: 26, color: 'var(--blue)', fontWeight: 700 }}>meetAI</div>
            </div>

            <div style={{ fontSize: 17, color: '#666', lineHeight: 1.5, maxWidth: 240 }}>
              말하기를 분석하고<br />더 나은 답변을 제안해드려요
            </div>
          </div>

          <div style={{
            fontSize: 13, color: 'var(--muted)', textAlign: 'center',
            border: '1.5px dashed var(--light-border)',
            borderRadius: 8, padding: '7px 12px',
          }}>
            공적 말하기 데이터셋 25,920건 기반
          </div>

          <button className="btn btn-primary" onClick={onStart}>
            시작하기
          </button>
        </div>
      </div>
    </div>
  )
}
