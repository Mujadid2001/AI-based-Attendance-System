# AI-Based Attendance System - Frontend

A modern, production-ready React frontend for the AI-based Attendance System. This frontend is **completely decoupled** from the backend and can work with any backend API by simply configuring the API URL.

## Features

- ✅ **Complete Decoupling**: No backend dependencies, works with any API
- ✅ **Modern Tech Stack**: React 18, TypeScript, Vite, TailwindCSS
- ✅ **JWT Authentication**: Secure token-based authentication with auto-refresh
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile
- ✅ **Role-Based Access**: Different views for students, teachers, and admins
- ✅ **Real-time Updates**: Face recognition and attendance marking
- ✅ **Production Ready**: Optimized build with code splitting

## Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running (see backend documentation)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` and set your backend API URL:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

Built files will be in `dist/` directory.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000/api` |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` |
| `VITE_APP_NAME` | Application name | `AI Attendance System` |
| `VITE_APP_VERSION` | Application version | `1.0.0` |
| `VITE_DEBUG` | Enable debug mode | `false` |

### Backend API Requirements

The frontend expects the backend to provide:

1. **JWT Authentication**:
   - `POST /api/token/` - Login and get tokens
   - `POST /api/token/refresh/` - Refresh access token
   - `POST /api/token/verify/` - Verify token

2. **CORS Configuration**:
   - Allow origin from your frontend domain
   - Allow credentials (`Access-Control-Allow-Credentials: true`)
   - Allow headers: `Authorization`, `Content-Type`

3. **API Endpoints**:
   - `/api/auth/*` - Authentication endpoints
   - `/api/students/*` - Student management
   - `/api/attendance/*` - Attendance management
   - `/api/ai/*` - Face recognition

See `API_DOCUMENTATION.md` in the backend directory for complete API reference.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── layout/         # Layout components
│   │   ├── ui/             # UI primitives
│   │   ├── ProtectedRoute.tsx
│   │   └── RoleBasedRoute.tsx
│   ├── pages/              # Page components
│   │   ├── auth/           # Login, Register
│   │   ├── students/       # Student management
│   │   ├── attendance/     # Attendance marking
│   │   ├── courses/        # Course management
│   │   ├── ai/             # Face recognition
│   │   ├── reports/        # Reports & analytics
│   │   ├── Dashboard.tsx
│   │   ├── Profile.tsx
│   │   └── Settings.tsx
│   ├── services/           # API service layer
│   │   ├── api.ts          # Axios instance & interceptors
│   │   ├── authService.ts
│   │   ├── studentService.ts
│   │   ├── attendanceService.ts
│   │   ├── courseService.ts
│   │   └── aiService.ts
│   ├── contexts/           # React contexts
│   │   └── AuthContext.tsx
│   ├── store/              # State management (Zustand)
│   │   └── authStore.ts
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── utils/              # Utility functions
│   │   ├── security.ts
│   │   └── rateLimit.ts
│   ├── config/             # Configuration files
│   │   └── security.ts
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── .env.example            # Environment variables example
├── .env.production.example # Production environment example
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Development

### Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Production build with optimizations
npm run build:production

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint code
npm run lint

# Clean build artifacts
npm run clean
```

### Code Organization

- **Services**: All API calls go through service files
- **Components**: Reusable UI components with TypeScript
- **Pages**: Route-level components
- **Types**: Centralized type definitions
- **Utils**: Helper functions and utilities

### State Management

- **Authentication**: Context API + Zustand
- **Local State**: React hooks (useState, useReducer)
- **Server State**: React Query (optional, not included)

## Deployment

### Option 1: Static Hosting (Vercel, Netlify)

1. Build the project:
```bash
npm run build
```

2. Configure environment variables in your hosting platform:
   - `VITE_API_URL` = Your production API URL

3. Deploy `dist/` directory

**Vercel Example**:
```bash
npm install -g vercel
vercel --prod
```

**Netlify Example**:
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Option 2: Docker

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build --build-arg VITE_API_URL=https://api.yourdomain.com/api -t attendance-frontend .
docker run -p 80:80 attendance-frontend
```

### Option 3: Traditional Web Server

1. Build the project:
```bash
npm run build
```

2. Copy `dist/` contents to your web server:
```bash
# Apache
cp -r dist/* /var/www/html/

# Nginx
cp -r dist/* /usr/share/nginx/html/
```

3. Configure web server for SPA routing:

**Nginx** (`/etc/nginx/sites-available/default`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Apache** (`.htaccess`):
```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

## Environment-Specific Configuration

### Development
```env
VITE_API_URL=http://localhost:8000/api
VITE_DEBUG=true
```

### Staging
```env
VITE_API_URL=https://api-staging.yourdomain.com/api
VITE_DEBUG=false
```

### Production
```env
VITE_API_URL=https://api.yourdomain.com/api
VITE_DEBUG=false
```

## Security Considerations

1. **API Communication**: All API calls use HTTPS in production
2. **JWT Tokens**: Stored in localStorage with auto-refresh
3. **CORS**: Backend must allow your frontend domain
4. **Input Validation**: All forms have client-side validation
5. **XSS Protection**: React automatically escapes content
6. **Content Security Policy**: Configure via headers

## Performance Optimization

- **Code Splitting**: Automatic by Vite
- **Lazy Loading**: Route-based code splitting
- **Image Optimization**: Use WebP format
- **Bundle Size**: ~200KB gzipped
- **Lighthouse Score**: 90+ (Performance, Accessibility, Best Practices)

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS 12+, Android 8+

## Troubleshooting

### Cannot connect to API

1. Check `VITE_API_URL` in `.env`
2. Verify backend is running
3. Check CORS configuration on backend
4. Check browser console for errors

### Authentication Issues

1. Clear localStorage and try again
2. Check JWT token expiry settings
3. Verify `/api/token/refresh/` endpoint works

### Build Errors

1. Clear node_modules: `rm -rf node_modules`
2. Clear cache: `npm cache clean --force`
3. Reinstall: `npm install`
4. Check Node.js version: `node --version` (should be 16+)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## License

[Your License Here]

## Support

For issues or questions:
- Backend API: See `attendance_system/API_DOCUMENTATION.md`
- Frontend: Create an issue on GitHub
- Email: support@yourdomain.com
