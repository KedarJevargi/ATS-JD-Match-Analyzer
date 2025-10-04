# ATS Resume Analyzer - Frontend

A modern, responsive React TypeScript application for analyzing resumes against job descriptions using AI-powered ATS (Applicant Tracking System) analysis.

## Features

- 🎨 **Modern UI Design**: Clean, minimalist interface with gradient backgrounds and smooth animations
- 📱 **Fully Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- 🔒 **Type Safety**: Built with TypeScript for enhanced code quality and developer experience
- 📤 **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- 📊 **Visual Results**: Beautiful visualization of analysis results with score cards and compliance checks
- ⚡ **Real-time Feedback**: Loading states, error handling, and instant user feedback
- ♿ **Accessible**: Follows accessibility best practices with proper ARIA labels and keyboard navigation

## Tech Stack

- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: CSS3 with modern features (Grid, Flexbox, Custom Properties)
- **HTTP Client**: Fetch API

## Project Structure

```
client/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── FileUpload.tsx           # PDF file upload component
│   │   ├── JobDescriptionInput.tsx  # Job description textarea
│   │   ├── AnalysisResults.tsx      # Results display component
│   │   ├── LoadingSpinner.tsx       # Loading indicator
│   │   └── ErrorMessage.tsx         # Error display component
│   ├── services/             # API service layer
│   │   └── api.ts                   # API client with all endpoints
│   ├── types/                # TypeScript type definitions
│   │   └── api.ts                   # API response types
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html              # HTML template
├── tsconfig.json           # TypeScript configuration
├── vite.config.js          # Vite configuration with backend proxy
└── package.json            # Dependencies and scripts
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend server running on port 8000

### Installation

```bash
# Navigate to client directory
cd client

# Install dependencies
npm install
```

### Development

```bash
# Start development server (with backend proxy)
npm run dev

# The app will be available at http://localhost:5173
```

The development server is configured to proxy API requests to `http://localhost:8000` (backend server).

### Build

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

### Linting

```bash
# Run ESLint
npm run lint
```

## API Integration

The application integrates with three backend endpoints:

### 1. Analyze Resume
- **Endpoint**: `POST /ats/analyse`
- **Purpose**: Analyze resume PDF against job description
- **Parameters**: 
  - `pdf`: Resume PDF file
  - `jd`: Job description text

### 2. Parse Job Description
- **Endpoint**: `POST /jds/parse_text`
- **Purpose**: Extract and structure keywords from job description
- **Parameters**: 
  - `jd`: Job description text

### 3. Extract PDF Text
- **Endpoint**: `POST /pdfs/extracttext`
- **Purpose**: Extract text content from PDF file
- **Parameters**: 
  - `pdf`: PDF file

## Environment Variables

Create a `.env` file in the client directory (optional):

```env
VITE_API_BASE_URL=http://localhost:8000
```

If not set, the application defaults to `http://localhost:8000`.

## Design System

### Colors
- Primary: `#6366f1` (Indigo)
- Success: `#059669` (Green)
- Warning: `#fb923c` (Orange)
- Error: `#dc2626` (Red)
- Background Gradient: `#667eea` to `#764ba2`

### Typography
- Font Family: Inter, system fonts fallback
- Headings: 600-700 weight
- Body: 400 weight

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
