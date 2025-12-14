# AI Attendance System - Frontend

Modern, responsive React frontend for the AI-based Attendance System with facial recognition capabilities.

## 🚀 Tech Stack

- **React 18** with TypeScript
- **Vite** - Lightning fast build tool
- **TailwindCSS** - Utility-first CSS framework
- **Framer Motion** - Smooth animations
- **Zustand** - State management
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Hook Form** - Form handling
- **React Hot Toast** - Notifications

## 📋 Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on http://localhost:8000

## 🛠️ Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your API URL (default: http://localhost:8000/api)

4. **Start development server:**
   ```bash
   npm run dev
   ```

   Frontend will run on http://localhost:3000

## 📜 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ui/           # Basic UI elements (Button, Input, Card, etc.)
│   │   ├── layout/       # Layout components (Sidebar, Header)
│   │   └── ProtectedRoute.tsx
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom hooks
│   ├── pages/            # Page components
│   │   ├── auth/         # Authentication pages
│   │   ├── students/     # Student management
│   │   ├── courses/      # Course management
│   │   ├── attendance/   # Attendance tracking
│   │   ├── ai/           # Face recognition features
│   │   └── reports/      # Reports & analytics
│   ├── services/         # API services
│   ├── store/            # Zustand state management
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
└── package.json
```

## 🎨 Features

### Authentication
- Login / Register
- JWT token management with refresh
- Password reset functionality
- Protected routes

### Dashboard
- Real-time statistics
- Today's attendance overview
- Quick action cards

### Student Management
- View all students
- Student profiles
- Face registration status
- Search and filter

### Course Management
- Course listing
- Course details
- Enrollment management

### Attendance
- Session management
- Attendance marking
- Real-time updates

### AI Features
- **Face Recognition** - Mark attendance using camera
- **Face Registration** - Register student faces
- Live camera preview
- Multiple image capture
- Confidence scoring

### UI/UX
- Fully responsive design
- Smooth animations with Framer Motion
- Modern gradient designs
- Toast notifications
- Loading states
- Error handling

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=AI Attendance System
VITE_APP_VERSION=1.0.0
```

### Path Aliases

Configured in `vite.config.ts` and `tsconfig.json`:

- `@/` - src/
- `@components/` - src/components/
- `@pages/` - src/pages/
- `@services/` - src/services/
- `@hooks/` - src/hooks/
- `@utils/` - src/utils/
- `@types/` - src/types/
- `@store/` - src/store/
- `@assets/` - src/assets/

## 📱 Responsive Design

- **Mobile First** - Optimized for all screen sizes
- **Breakpoints:**
  - sm: 640px
  - md: 768px
  - lg: 1024px
  - xl: 1280px
  - 2xl: 1536px

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

This creates an optimized build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Deploy to Vercel/Netlify

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Add environment variables

## 🔐 Security

- JWT tokens stored in localStorage
- Automatic token refresh
- Protected routes with authentication check
- CORS configured for API communication

## 🎯 Best Practices

- **TypeScript** - Full type safety
- **Component Organization** - Modular and reusable
- **State Management** - Zustand for global state
- **API Layer** - Centralized service layer
- **Error Handling** - Consistent error messages
- **Loading States** - User feedback for async operations

## 📞 API Integration

The frontend communicates with the Django backend via REST API:

- Base URL: `http://localhost:8000/api`
- Authentication: JWT Bearer tokens
- Endpoints:
  - `/auth/*` - Authentication
  - `/students/*` - Student management
  - `/courses/*` - Course management
  - `/attendance/*` - Attendance tracking
  - `/ai/*` - Face recognition

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety
3. Follow naming conventions
4. Add proper error handling
5. Test responsive design

## 📄 License

This project is part of the AI-based Attendance System.
