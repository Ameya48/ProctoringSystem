import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Frontend event detection hook:
 * - Screen capture start/stop (getDisplayMedia)
 * - Tab switching (visibilitychange)
 * - Fullscreen exit (fullscreenchange)
 * - Browser minimize / app switch approximation (window blur/focus)
 * - Inactivity (idle timer based on input events)
 */
export default function useScreenMonitoring({ idleMs = 15000 } = {}) {
  const [screenStream, setScreenStream] = useState(null)
  const [isIdle, setIsIdle] = useState(false)

  const lastActivityRef = useRef(Date.now())
  const idleIntervalRef = useRef(null)
  const startedAtRef = useRef(null)

  const emitRef = useRef(() => {})

  const setEmitter = useCallback((fn) => {
    emitRef.current = fn || (() => {})
  }, [])

  const emit = useCallback((event_type, details = {}) => {
    emitRef.current({ event_type, details })
  }, [])

  const markActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
    if (isIdle) {
      setIsIdle(false)
      emit('activity_resumed', {})
    }
  }, [emit, isIdle])

  const startScreenShare = useCallback(async () => {
    const startedAt = Date.now()
    startedAtRef.current = startedAt
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: { ideal: 10, max: 15 } },
        audio: false
      })

      setScreenStream(stream)
      emit('screen_share_started', {})

      const [track] = stream.getVideoTracks()
      if (track) {
        track.onended = () => {
          const duration_ms = startedAtRef.current ? Date.now() - startedAtRef.current : undefined
          emit('screen_share_stopped', { duration_ms })
          setScreenStream(null)
        }
      }
      return stream
    } catch (err) {
      throw err
    }
  }, [emit])

  const stopScreenShare = useCallback(() => {
    if (!screenStream) return
    try {
      screenStream.getTracks().forEach((t) => t.stop())
    } catch {
      // ignore
    }
    setScreenStream(null)
  }, [screenStream])

  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') emit('tab_hidden', {})
      if (document.visibilityState === 'visible') emit('tab_visible', {})
    }
    const onFullscreen = () => {
      // if previously in fullscreen and now exited, flag it
      if (!document.fullscreenElement) emit('fullscreen_exited', {})
    }
    const onBlur = () => emit('window_blur', {})
    const onFocus = () => emit('window_focus', {})

    document.addEventListener('visibilitychange', onVisibility)
    document.addEventListener('fullscreenchange', onFullscreen)
    window.addEventListener('blur', onBlur)
    window.addEventListener('focus', onFocus)

    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      document.removeEventListener('fullscreenchange', onFullscreen)
      window.removeEventListener('blur', onBlur)
      window.removeEventListener('focus', onFocus)
    }
  }, [emit])

  useEffect(() => {
    const activityEvents = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll']
    const handler = () => markActivity()
    activityEvents.forEach((e) => window.addEventListener(e, handler, { passive: true }))

    idleIntervalRef.current = setInterval(() => {
      const delta = Date.now() - lastActivityRef.current
      if (!isIdle && delta >= idleMs) {
        setIsIdle(true)
        emit('idle', { duration_ms: delta })
      }
    }, 1000)

    return () => {
      activityEvents.forEach((e) => window.removeEventListener(e, handler))
      if (idleIntervalRef.current) clearInterval(idleIntervalRef.current)
      idleIntervalRef.current = null
    }
  }, [emit, idleMs, isIdle, markActivity])

  return {
    screenStream,
    isIdle,
    setEmitter,
    startScreenShare,
    stopScreenShare
  }
}

