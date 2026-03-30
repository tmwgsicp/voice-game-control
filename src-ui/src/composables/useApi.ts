/**
 * Copyright (C) 2026 VoiceGameControl Contributors
 * Licensed under MIT
 */

import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'

const backendPort = ref(0)
const baseUrl = ref('')

let _initialized = false

export async function initApi() {
  if (_initialized) return
  
  const isWebMode = typeof window !== 'undefined' && !window.__TAURI__
  
  try {
    if (isWebMode) {
      const port = 18234
      backendPort.value = port
      baseUrl.value = `http://127.0.0.1:${port}`
      _initialized = true
      console.log(`API initialized (Web mode): ${baseUrl.value}`)
    } else {
      console.log('Initializing API, fetching port from Tauri...')
      const port = await invoke<number>('get_port')
      backendPort.value = port
      baseUrl.value = `http://127.0.0.1:${port}`
      _initialized = true
      console.log(`API initialized (Tauri mode): ${baseUrl.value}`)
    }
  } catch (error) {
    console.error('Failed to initialize API:', error)
    baseUrl.value = 'http://127.0.0.1:18234'
    console.warn('Using fallback URL:', baseUrl.value)
  }
}

export function useApi() {
  async function fetchJson<T = any>(path: string, options?: RequestInit): Promise<T> {
    if (!baseUrl.value) await initApi()
    if (!baseUrl.value) {
      throw new Error('后端服务未就绪')
    }
    
    const url = `${baseUrl.value}${path}`
    console.log(`API request: ${options?.method || 'GET'} ${url}`)
    
    const resp = await fetch(url, options)
    if (!resp.ok) {
      const error = await resp.json().catch(() => ({ detail: 'Request failed' }))
      throw error
    }
    return resp.json()
  }

  async function get<T = any>(path: string): Promise<T> {
    return fetchJson(path)
  }

  async function post<T = any>(path: string, data?: any): Promise<T> {
    return fetchJson(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async function put<T = any>(path: string, data?: any): Promise<T> {
    return fetchJson(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async function del<T = any>(path: string): Promise<T> {
    return fetchJson(path, {
      method: 'DELETE',
    })
  }

  return {
    baseUrl,
    backendPort,
    get,
    post,
    put,
    del,
  }
}
