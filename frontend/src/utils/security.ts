/**
 * Security utility functions for input sanitization and validation
 */

/**
 * Sanitize string input to prevent XSS attacks
 * @param input - String to sanitize
 * @returns Sanitized string
 */
export const sanitizeInput = (input: string): string => {
  if (!input) return ''
  
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
}

/**
 * Sanitize object with string values
 * @param obj - Object to sanitize
 * @returns Sanitized object
 */
export const sanitizeObject = <T extends Record<string, any>>(obj: T): T => {
  const sanitized = { ...obj } as Record<string, any>
  
  Object.keys(sanitized).forEach((key) => {
    if (typeof sanitized[key] === 'string') {
      sanitized[key] = sanitizeInput(sanitized[key])
    }
  })
  
  return sanitized as T
}

/**
 * Validate email format
 * @param email - Email to validate
 * @returns True if valid email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i
  return emailRegex.test(email)
}

/**
 * Validate password strength
 * @param password - Password to validate
 * @returns Object with validation result and message
 */
export const validatePasswordStrength = (password: string): { isValid: boolean; message?: string } => {
  if (password.length < 8) {
    return { isValid: false, message: 'Password must be at least 8 characters long' }
  }
  
  if (!/[a-z]/.test(password)) {
    return { isValid: false, message: 'Password must contain at least one lowercase letter' }
  }
  
  if (!/[A-Z]/.test(password)) {
    return { isValid: false, message: 'Password must contain at least one uppercase letter' }
  }
  
  if (!/\d/.test(password)) {
    return { isValid: false, message: 'Password must contain at least one number' }
  }
  
  if (!/[@$!%*?&]/.test(password)) {
    return { isValid: false, message: 'Password must contain at least one special character (@$!%*?&)' }
  }
  
  return { isValid: true }
}

/**
 * Validate username format
 * @param username - Username to validate
 * @returns True if valid username
 */
export const isValidUsername = (username: string): boolean => {
  const usernameRegex = /^[a-zA-Z0-9_]{3,}$/
  return usernameRegex.test(username)
}

/**
 * Escape HTML special characters
 * @param text - Text to escape
 * @returns Escaped text
 */
export const escapeHtml = (text: string): string => {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  }
  
  return text.replace(/[&<>"'/]/g, (char) => map[char])
}

/**
 * Check if string contains SQL injection patterns
 * @param input - String to check
 * @returns True if suspicious patterns detected
 */
export const hasSqlInjectionPattern = (input: string): boolean => {
  const sqlPatterns = [
    /(\bor\b|\band\b).*?=/i,
    /union.*?select/i,
    /insert.*?into/i,
    /delete.*?from/i,
    /drop.*?table/i,
    /update.*?set/i,
    /--/,
    /;.*?--/,
    /\/\*.*?\*\//,
  ]
  
  return sqlPatterns.some((pattern) => pattern.test(input))
}

/**
 * Remove role-related fields from user input (security measure)
 * @param data - User data object
 * @returns Sanitized data without role fields
 */
export const removeRoleFields = <T extends Record<string, any>>(data: T): Omit<T, 'role' | 'is_admin' | 'is_staff' | 'is_superuser'> => {
  const sanitized = { ...data }
  delete sanitized.role
  delete sanitized.is_admin
  delete sanitized.is_staff
  delete sanitized.is_superuser
  return sanitized
}
