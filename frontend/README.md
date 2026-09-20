# Competitor Intelligence Frontend

A production-quality SaaS dashboard built with Next.js 15, React 19, and Tailwind CSS.

## Tech Stack

- **Next.js 15** - React framework with App Router
- **React 19** - Latest React with server components
- **JavaScript** - No TypeScript dependency
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client with JWT interceptor
- **React Hook Form** - Form management
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icons
- **Recharts** - Data visualization
- **React Hot Toast** - Toast notifications

## Features

- 🔐 **Authentication** - JWT-based auth with automatic token refresh
- 🎨 **Modern UI** - Glassmorphism, rounded cards, smooth animations
- 🌙 **Theme Support** - Light/dark mode with system preference
- 📱 **Responsive** - Mobile-first design
- ⚡ **Performance** - Optimized loading states and skeletons
- 🛡️ **Protected Routes** - Route-based authentication
- 🔄 **API Integration** - Centralized API client with interceptors

## Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── auth/           # Authentication pages
│   ├── dashboard/      # Dashboard pages
│   └── layout.js       # Root layout
├── components/         # Reusable components
│   ├── layout/        # Layout components
│   ├── ui/            # UI components
│   └── forms/         # Form components
├── contexts/          # React contexts
├── hooks/             # Custom hooks
├── services/          # API services
├── styles/            # Global styles
└── utils/             # Utility functions
```

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
```

3. Update environment variables in `.env.local`

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - Application name
- `NEXT_PUBLIC_APP_VERSION` - Application version

## Development Guidelines

- Use functional components with hooks
- Implement proper error boundaries
- Follow responsive design principles
- Use semantic HTML elements
- Maintain consistent spacing and typography
- Implement loading states for better UX
- Use proper TypeScript types (if migrating)

## Building for Production

```bash
npm run build
npm start
```

## API Integration

The frontend integrates with the FastAPI backend running on `http://127.0.0.1:8000`. All API calls include automatic JWT token management and error handling.