import { defineConfig, type PluginOption } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'
import mkcert from 'vite-plugin-mkcert'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  // vite-plugin-mkcert generates and installs a local root CA certificate so
  // the dev server can serve https (needed for getUserMedia/camera access on
  // a non-localhost origin). It shells out to `mkcert`, which requires root.
  //
  // It must therefore never load during `vite build`: Vercel's build
  // containers run as a non-root user with no CA store to write to, so
  // including the plugin unconditionally makes every production build fail
  // with a permission error before a single module is bundled.
  //
  // `command` is 'serve' for `vite` and `vite preview`, and 'build' for
  // `vite build`, which is exactly the distinction we need.
  const isDevServer = command === 'serve'

  return {
    plugins: [
      react(),
      // `false` is the documented way to disable a plugin conditionally.
      ...(isDevServer ? [mkcert() as PluginOption] : []),
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
        '@components': resolve(__dirname, './src/components'),
        '@pages': resolve(__dirname, './src/pages'),
        '@services': resolve(__dirname, './src/services'),
        '@hooks': resolve(__dirname, './src/hooks'),
        '@utils': resolve(__dirname, './src/utils'),
        '@types': resolve(__dirname, './src/types'),
        '@store': resolve(__dirname, './src/store'),
        '@assets': resolve(__dirname, './src/assets'),
      },
    },
    server: {
      // Only meaningful with the mkcert plugin above; enabling https without a
      // certificate would make the dev server refuse to start.
      https: isDevServer,
      port: 3000,
      // No proxy - frontend is completely decoupled from backend.
      // Configure the API URL via VITE_API_URL.
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      // Optimize for production
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['framer-motion', 'react-icons'],
            'form-vendor': ['react-hook-form', 'react-hot-toast'],
          },
        },
      },
      // Increase chunk size warning limit
      chunkSizeWarningLimit: 1000,
    },
    preview: {
      https: isDevServer,
      port: 3000,
    },
  }
})
