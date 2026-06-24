import { useState } from 'react'
import { supabase } from '../supabase'

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
    <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
  </svg>
)

const Divider = () => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--muted)', fontSize: 13 }}>
    <span style={{ flex: 1, borderTop: '1.5px dashed var(--light-border)' }} />
    또는
    <span style={{ flex: 1, borderTop: '1.5px dashed var(--light-border)' }} />
  </div>
)

export default function LoginPage({ onRegister }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { error: err } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (err) setError(err.message === 'Invalid login credentials' ? '이메일 또는 비밀번호가 올바르지 않습니다.' : err.message)
  }

  const handleGoogle = async () => {
    setGoogleLoading(true)
    setError(null)
    const { error: err } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin,
        queryParams: { prompt: 'select_account' },
      },
    })
    if (err) { setError(err.message); setGoogleLoading(false) }
  }

  const inputStyle = {
    border: '2px solid var(--border)',
    borderRadius: 8,
    padding: '10px 12px',
    fontSize: 15,
    fontFamily: 'var(--font)',
    outline: 'none',
    background: '#faf9f4',
  }

  return (
    <div className="page-wrap" style={{ justifyContent: 'center' }}>
      <div className="screen">
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 36, fontFamily: 'var(--font-accent)', color: 'var(--blue)', marginBottom: 4 }}>meetAI</div>
            <div style={{ fontSize: 14, color: 'var(--muted)' }}>면접·발표 코칭 서비스</div>
          </div>

          <div style={{ fontSize: 20, fontWeight: 700 }}>로그인</div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--muted)' }}>이메일</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com" required style={inputStyle} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--muted)' }}>비밀번호</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호" required style={inputStyle} />
            </div>

            {error && (
              <div style={{ background: '#fff3f0', border: '1.5px solid var(--orange)', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: 'var(--orange)' }}>
                {error}
              </div>
            )}

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ opacity: loading ? 0.6 : 1 }}>
              {loading ? '로그인 중…' : '로그인'}
            </button>
          </form>

          <Divider />

          <button
            onClick={handleGoogle}
            disabled={googleLoading}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              border: '2px solid var(--border)',
              borderRadius: 10,
              padding: '11px 16px',
              background: '#fff',
              fontFamily: 'var(--font)',
              fontSize: 15,
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '2px 2px 0 rgba(43,43,43,0.08)',
              opacity: googleLoading ? 0.6 : 1,
              transition: 'box-shadow 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '3px 3px 0 rgba(43,43,43,0.15)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = '2px 2px 0 rgba(43,43,43,0.08)'}
          >
            <GoogleIcon />
            {googleLoading ? '이동 중…' : 'Google로 로그인'}
          </button>

          <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--muted)' }}>
            계정이 없으신가요?{' '}
            <button onClick={onRegister} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontFamily: 'var(--font)', fontSize: 13, fontWeight: 700, textDecoration: 'underline' }}>
              회원가입
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
