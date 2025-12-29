/**
 * Security Configuration
 * Centralized security settings and environment variables
 */

export const securityConfig = {
  // API Configuration
  api: {
    baseUrl: (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api',
    timeout: 30000,
    withCredentials: true,
  },

  // Password Requirements
  password: {
    minLength: 8,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    specialChars: '@$!%*?&',
  },

  // Username Requirements
  username: {
    minLength: 3,
    maxLength: 30,
    allowedPattern: /^[a-zA-Z0-9_]+$/,
  },

  // Session Configuration
  session: {
    tokenKey: 'accessToken',
    refreshTokenKey: 'refreshToken',
    userKey: 'user',
  },

  // Rate Limiting (client-side hints)
  rateLimit: {
    maxLoginAttempts: 5,
    lockoutDuration: 15 * 60 * 1000, // 15 minutes
  },

  // Allowed roles for registration
  allowedRegistrationRoles: ['student', 'teacher'] as const,

  // Content Security Policy
  csp: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'unsafe-inline'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", 'data:', 'https:'],
    connectSrc: ["'self'", (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'],
  },
}

// Validate environment variables
const validateEnv = () => {
  const requiredEnvVars: string[] = []
  
  const missingVars = requiredEnvVars.filter(
    (varName) => !(import.meta.env[varName as keyof ImportMetaEnv] as string)
  )
  
  if (missingVars.length > 0) {
    console.warn(
      `Missing optional environment variables: ${missingVars.join(', ')}`
    )
  }
}

// Type for ImportMeta environment
interface ImportMetaEnv {
  VITE_API_URL: string
  VITE_API_TIMEOUT: string
}

declare global {
  interface ImportMeta {
    readonly env: ImportMetaEnv & Record<string, string | undefined>
  }
}

// Run validation on load
validateEnv()

export default securityConfig
