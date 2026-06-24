import { getAccessToken } from './supabase'

async function authHeaders(extra = {}) {
  const token = await getAccessToken()
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra
}

export async function uploadAudio(file, { contextMode, expectedDurationSec, role, keywords }) {
  const form = new FormData()
  form.append('file', file)
  const params = new URLSearchParams()
  params.set('context_mode', contextMode)
  if (expectedDurationSec) params.set('expected_duration_sec', String(expectedDurationSec))
  if (role) params.set('role', role)
  if (keywords?.length) params.set('keywords', keywords.join(','))

  const res = await fetch(`/upload/audio?${params}`, {
    method: 'POST',
    headers: await authHeaders(),
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `서버 오류 (${res.status})`)
  }
  return res.json()
}

export async function analyzeFull(file, { contextMode, expectedDurationSec, role, keywords }, nonverbalEvents) {
  // 1. STT + 언어 분석 (history_id 포함하여 반환)
  const audioData = await uploadAudio(file, { contextMode, expectedDurationSec, role, keywords })

  // 2. 통합 분석 (기존 history 레코드 업데이트)
  const res = await fetch('/analyze/full', {
    method: 'POST',
    headers: await authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      context_mode: contextMode,
      history_id: audioData.history_id ?? null,
      language: {
        transcript: audioData.transcript,
        context_mode: contextMode,
        expected_duration_sec: expectedDurationSec,
        role: role,
        keywords: keywords || [],
      },
      nonverbal: {
        context_mode: contextMode,
        clip_duration_sec: audioData.audio_duration_sec || expectedDurationSec || 60.0,
        ...nonverbalEvents,
      },
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `통합 분석 오류 (${res.status})`)
  }
  const fullResult = await res.json()
  return {
    ...fullResult,
    transcript: audioData.transcript,
    audio_duration_sec: audioData.audio_duration_sec,
    pronunciation_score: audioData.pronunciation_score,
    pronunciation_score_100: audioData.pronunciation_score_100,
    pronunciation_grade: audioData.pronunciation_grade,
  }
}
