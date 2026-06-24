import { useState, useEffect } from 'react'
import { supabase, getAccessToken, uploadVideo } from './supabase'
import EntryPage from './pages/EntryPage'
import ModeSelectPage from './pages/ModeSelectPage'
import SetupPage from './pages/SetupPage'
import RecordPage from './pages/RecordPage'
import AnalyzingPage from './pages/AnalyzingPage'
import ResultPage from './pages/ResultPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

export default function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authPage, setAuthPage] = useState('login') // 'login' | 'register'
  const [emailVerified, setEmailVerified] = useState(false)

  const [page, setPage] = useState('entry')
  const [mode, setMode] = useState(null)
  const [setup, setSetup] = useState({})
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    // 이메일 인증 후 리다이렉트 감지 (URL 해시에 type=signup 포함)
    const hash = window.location.hash
    if (hash.includes('type=signup') || hash.includes('type=email_change')) {
      setEmailVerified(true)
      window.history.replaceState(null, '', window.location.pathname)
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setAuthLoading(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })
    return () => subscription.unsubscribe()
  }, [])

  const go = (p) => setPage(p)

  const handleModeSelect = (m) => { setMode(m); go('setup') }
  const handleSetup = (s) => { setSetup(s); go('record') }

  const handleAnalyze = async (file, videoBlob) => {
    go('analyzing')
    setError(null)
    try {
      const { uploadAudio, analyzeFull } = await import('./api.js')
      const options = {
        contextMode: mode === 'interview' ? 'interview' : 'presentation',
        expectedDurationSec: setup.durationSec,
        role: setup.role,
        keywords: setup.keywords,
      }

      let res
      if (setup.enableNonverbal) {
        let nonverbalEvents = { hand_movement_events: 3, head_movement_events: 2, posture_shift_events: 1, meaningless_gesture_events: 1 }
        if (setup.nonverbalStyle === 'stable') {
          nonverbalEvents = { hand_movement_events: 2, head_movement_events: 1, posture_shift_events: 1, meaningless_gesture_events: 0 }
        } else if (setup.nonverbalStyle === 'active_hands') {
          nonverbalEvents = { hand_movement_events: 13, head_movement_events: 2, posture_shift_events: 1, meaningless_gesture_events: 5 }
        } else if (setup.nonverbalStyle === 'unstable') {
          nonverbalEvents = { hand_movement_events: 5, head_movement_events: 9, posture_shift_events: 7, meaningless_gesture_events: 3 }
        }
        res = await analyzeFull(file, options, nonverbalEvents)
      } else {
        res = await uploadAudio(file, options)
      }

      // 영상 업로드 (로그인 + 영상 있을 때)
      if (user && videoBlob && res.history_id) {
        try {
          const videoPath = await uploadVideo(user.id, videoBlob)
          await fetch(`/history/${res.history_id}/video`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${await getAccessToken()}`,
            },
            body: JSON.stringify({ video_path: videoPath }),
          })
        } catch (videoErr) {
          console.warn('영상 업로드 실패 (분석 결과는 저장됨):', videoErr)
        }
      }

      setResult(res)
      go('result')
    } catch (e) {
      setError(e.message)
      go('record')
    }
  }

  const restart = () => { setResult(null); setError(null); go('record') }
  const reset = () => { setResult(null); setError(null); setSetup({}); setMode(null); go('entry') }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    reset()
  }

  if (authLoading) {
    return (
      <div className="page-wrap" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="spinner-lg" />
      </div>
    )
  }

  // 이메일 인증 완료 화면
  if (emailVerified && !user) {
    return (
      <div className="page-wrap" style={{ justifyContent: 'center' }}>
        <div className="screen">
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16, textAlign: 'center', alignItems: 'center' }}>
            <div style={{ fontSize: 56 }}>✅</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>이메일 인증 완료!</div>
            <div style={{ fontSize: 14, color: 'var(--muted)', lineHeight: 1.7 }}>
              이메일 인증이 완료되었습니다.<br />
              이제 로그인할 수 있습니다.
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={() => { setEmailVerified(false); setAuthPage('login') }}
            >
              로그인하러 가기
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!user) {
    return authPage === 'register'
      ? <RegisterPage onLogin={() => setAuthPage('login')} />
      : <LoginPage onRegister={() => setAuthPage('register')} />
  }

  // 유저 정보 헤더 (항상 표시)
  const username = (user.user_metadata || {}).username || user.email?.split('@')[0] || '유저'

  return (
    <>
      {/* 상단 네비게이션 바 */}
      {page !== 'analyzing' && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 200,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '8px 16px',
          background: 'rgba(250, 249, 244, 0.95)',
          borderBottom: '1.5px solid var(--border)',
          backdropFilter: 'blur(6px)',
        }}>
          <span
            style={{ fontFamily: 'var(--font-accent)', fontSize: 18, color: 'var(--blue)', cursor: 'pointer' }}
            onClick={reset}
          >
            meetAI
          </span>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>{username}</span>
            <button
              className="btn"
              style={{ fontSize: 12, padding: '4px 10px', border: '1.5px solid var(--border)' }}
              onClick={() => go('history')}
            >
              기록
            </button>
            <button
              className="btn"
              style={{ fontSize: 12, padding: '4px 10px', border: '1.5px solid var(--border)', color: 'var(--muted)' }}
              onClick={handleLogout}
            >
              로그아웃
            </button>
          </div>
        </div>
      )}

      {/* 페이지 콘텐츠 (헤더 높이만큼 패딩) */}
      <div style={{ paddingTop: page !== 'analyzing' ? 48 : 0 }}>
        {page === 'entry' && <EntryPage onStart={() => go('mode')} />}
        {page === 'mode' && <ModeSelectPage onSelect={handleModeSelect} onBack={() => go('entry')} />}
        {page === 'setup' && <SetupPage mode={mode} onNext={handleSetup} onBack={() => go('mode')} />}
        {page === 'record' && (
          <RecordPage
            mode={mode}
            setup={setup}
            error={error}
            onAnalyze={handleAnalyze}
            onBack={() => go('setup')}
          />
        )}
        {page === 'analyzing' && <AnalyzingPage />}
        {page === 'result' && result && (
          <ResultPage result={result} mode={mode} setup={setup} onRestart={restart} onExit={reset} />
        )}
        {page === 'history' && (
          <HistoryPage
            onBack={() => go('entry')}
            onViewResult={(res, histMode) => {
              setResult(res)
              setMode(histMode)
              go('result')
            }}
          />
        )}
      </div>
    </>
  )
}
