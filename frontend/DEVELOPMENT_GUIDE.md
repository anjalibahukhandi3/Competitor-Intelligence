# Development Guide - Competitor Intelligence Frontend

## 🚀 Quick Start

1. **Install Node.js** (v18 or higher)
2. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```
3. **Environment setup:**
   ```bash
   cp .env.example .env.local
   # Update NEXT_PUBLIC_API_BASE_URL if needed
   ```
4. **Start development server:**
   ```bash
   npm run dev
   ```
5. **Open** [http://localhost:3000](http://localhost:3000)

## 🧪 Testing Checklist

### ✅ Authentication Flow
- [ ] Navigate to root `/` → redirects to login
- [ ] Login page renders correctly
- [ ] Register page renders correctly  
- [ ] Forgot password page renders correctly
- [ ] Form validation works (required fields, email format, password strength)
- [ ] Theme toggle works on auth pages
- [ ] Responsive design on mobile devices
- [ ] Login with demo credentials (if backend running)
- [ ] Successful login redirects to dashboard
- [ ] Protected routes work (redirect to login when not authenticated)

### ✅ Dashboard Layout
- [ ] Sidebar navigation works
- [ ] Mobile sidebar toggle works
- [ ] Navbar renders with user info
- [ ] Theme toggle in navbar works
- [ ] Search bar displays
- [ ] Profile dropdown works
- [ ] Logout functionality works
- [ ] Responsive layout on all screen sizes

### ✅ Dashboard Components
- [ ] Stats cards display with animations
- [ ] Analytics chart renders with Recharts
- [ ] Recent reports section displays
- [ ] Latest competitors section displays
- [ ] Recent activity feed displays
- [ ] Quick actions panel works
- [ ] All animations and transitions work smoothly
- [ ] Cards have hover effects
- [ ] Loading states work

### ✅ Navigation Pages
- [ ] Dashboard page loads completely
- [ ] Competitors page shows empty state
- [ ] Reports page shows empty state
- [ ] Monitoring page shows empty state
- [ ] Analytics page shows empty state
- [ ] Settings page renders with toggles
- [ ] All sidebar navigation links work
- [ ] Page transitions are smooth

### ✅ Theme & Responsive Design
- [ ] Light mode works correctly
- [ ] Dark mode works correctly
- [ ] Theme persists on page reload
- [ ] Mobile responsive (< 768px)
- [ ] Tablet responsive (768px - 1024px)
- [ ] Desktop responsive (> 1024px)
- [ ] Glassmorphism effects display correctly
- [ ] All animations work on different screen sizes

### ✅ Error Handling
- [ ] 404 page displays correctly
- [ ] Error boundaries work
- [ ] Form validation errors show
- [ ] Network error handling
- [ ] Loading spinners display
- [ ] Empty states display correctly

## 🔧 Development Notes

### Backend Integration
- The frontend is configured to work with the FastAPI backend at `http://127.0.0.1:8000`
- JWT authentication is implemented with automatic token refresh
- All API calls include proper error handling and loading states

### Key Features Implemented
1. **Authentication System**
   - JWT-based authentication with auto-refresh
   - Protected routes with middleware
   - Comprehensive form validation

2. **Modern UI/UX**
   - Production-quality SaaS design
   - Smooth Framer Motion animations
   - Glassmorphism and modern card designs
   - Responsive mobile-first approach

3. **Dashboard Features**
   - Real-time statistics cards
   - Interactive charts with Recharts
   - Activity feeds and recent updates
   - Quick action shortcuts

4. **Theme System**
   - Light/dark mode support
   - System preference detection
   - Persistent theme settings

### Architecture
- **Next.js 15** with App Router
- **React 19** with modern hooks
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Axios** for API communication
- **React Hook Form** for form management

## 🐛 Troubleshooting

### Common Issues

1. **Hydration Errors**
   - Check `suppressHydrationWarning` in layouts
   - Ensure theme is properly initialized

2. **API Connection**
   - Verify backend is running on port 8000
   - Check CORS settings if needed
   - Verify environment variables

3. **Build Issues**
   - Clear `.next` folder and rebuild
   - Check for TypeScript errors (should be none)
   - Verify all imports are correct

4. **Animation Performance**
   - Reduce motion for accessibility if needed
   - Check for memory leaks in useEffect hooks

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚢 Production Deployment

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Start production server:**
   ```bash
   npm start
   ```

3. **Environment variables for production:**
   - Update `NEXT_PUBLIC_API_BASE_URL` to production backend
   - Configure any additional environment variables

## 📊 Performance Considerations

- Images are optimized with Next.js Image component
- Code splitting is handled automatically by Next.js
- Framer Motion animations are optimized for performance
- Tailwind CSS is purged in production builds