/**
 * Rate Limiting Utility
 * Client-side rate limiting to prevent brute force attacks
 */

interface RateLimitData {
  attempts: number
  lockedUntil?: number
}

const RATE_LIMIT_STORAGE_KEY = 'rate_limit_data'

/**
 * Get rate limit data for a specific action
 */
const getRateLimitData = (action: string): RateLimitData => {
  try {
    const data = localStorage.getItem(`${RATE_LIMIT_STORAGE_KEY}_${action}`)
    return data ? JSON.parse(data) : { attempts: 0 }
  } catch {
    return { attempts: 0 }
  }
}

/**
 * Set rate limit data for a specific action
 */
const setRateLimitData = (action: string, data: RateLimitData): void => {
  try {
    localStorage.setItem(`${RATE_LIMIT_STORAGE_KEY}_${action}`, JSON.stringify(data))
  } catch (error) {
    console.error('Failed to set rate limit data:', error)
  }
}

/**
 * Check if action is rate limited
 */
export const isRateLimited = (action: string): { limited: boolean; remainingTime?: number } => {
  const data = getRateLimitData(action)
  
  if (data.lockedUntil && data.lockedUntil > Date.now()) {
    const remainingTime = Math.ceil((data.lockedUntil - Date.now()) / 1000)
    return { limited: true, remainingTime }
  }
  
  return { limited: false }
}

/**
 * Record a rate limit attempt
 */
export const recordAttempt = (
  action: string,
  maxAttempts: number = 5,
  lockoutDuration: number = 15 * 60 * 1000
): void => {
  const data = getRateLimitData(action)
  
  // Clear lockout if expired
  if (data.lockedUntil && data.lockedUntil < Date.now()) {
    data.attempts = 0
    data.lockedUntil = undefined
  }
  
  data.attempts += 1
  
  // Lock if max attempts exceeded
  if (data.attempts >= maxAttempts) {
    data.lockedUntil = Date.now() + lockoutDuration
  }
  
  setRateLimitData(action, data)
}

/**
 * Reset rate limit for action
 */
export const resetRateLimit = (action: string): void => {
  setRateLimitData(action, { attempts: 0 })
}

/**
 * Get remaining attempts before lockout
 */
export const getRemainingAttempts = (action: string, maxAttempts: number = 5): number => {
  const data = getRateLimitData(action)
  return Math.max(0, maxAttempts - data.attempts)
}
