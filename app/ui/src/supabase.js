import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function getAccessToken() {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

export async function uploadVideo(userId, videoBlob) {
  const path = `${userId}/${Date.now()}.webm`
  const { error } = await supabase.storage
    .from('meetai-videos')
    .upload(path, videoBlob, { contentType: 'video/webm', upsert: false })
  if (error) throw new Error(`영상 업로드 실패: ${error.message}`)
  return path
}

export async function getVideoSignedUrl(path) {
  if (!path) return null
  const { data, error } = await supabase.storage
    .from('meetai-videos')
    .createSignedUrl(path, 3600)
  return error ? null : data.signedUrl
}
