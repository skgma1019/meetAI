const ChatIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)

const PresentIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#6b6b6b" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 3h20v14H2z"/>
    <path d="M8 21h8M12 17v4"/>
  </svg>
)

const ModeCard = ({ icon, title, subtitle, onClick, style }) => (
  <button
    onClick={onClick}
    style={{
      border: '2px solid var(--border)',
      borderRadius: '13px 10px 14px 9px / 9px 13px 8px 13px',
      background: '#fff',
      boxShadow: 'var(--shadow-card)',
      padding: '16px',
      display: 'flex', alignItems: 'center', gap: 14,
      cursor: 'pointer', width: '100%', textAlign: 'left',
      fontFamily: 'var(--font)',
      transition: 'transform 0.1s, box-shadow 0.1s',
      ...style,
    }}
    onMouseDown={e => e.currentTarget.style.transform = 'translate(2px,2px)'}
    onMouseUp={e => e.currentTarget.style.transform = ''}
    onMouseLeave={e => e.currentTarget.style.transform = ''}
  >
    <div style={{
      width: 52, height: 52, flexShrink: 0,
      border: '1.5px solid var(--light-border)',
      borderRadius: 10,
      background: 'var(--stripe-bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {icon}
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 21, fontWeight: 700 }}>{title}</div>
      <div style={{ fontSize: 15, color: '#888' }}>{subtitle}</div>
    </div>
    <span style={{ fontSize: 26, color: 'var(--muted)' }}>›</span>
  </button>
)

export default function ModeSelectPage({ onSelect, onBack }) {
  return (
    <div className="page-wrap">
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="nav-bar">
            <button className="nav-back" onClick={onBack}>‹</button>
            <div className="dots">
              <div className="dot on" /><div className="dot off" /><div className="dot off" />
            </div>
            <div style={{ width: 30 }} />
          </div>

          <div style={{ marginTop: 4 }}>
            <div style={{ fontSize: 25, fontWeight: 700 }}>무엇을 연습할까요?</div>
            <div style={{ fontSize: 16, color: '#888' }}>모드를 선택하세요</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 6 }}>
            <ModeCard
              icon={<ChatIcon />}
              title="면접"
              subtitle="질문에 답하는 연습"
              onClick={() => onSelect('interview')}
            />
            <ModeCard
              icon={<PresentIcon />}
              title="발표"
              subtitle="주제를 설명하는 연습"
              onClick={() => onSelect('presentation')}
              style={{ borderRadius: '11px 14px 9px 13px / 13px 9px 13px 8px' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
