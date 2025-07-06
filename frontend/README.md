# Web Search Agent Frontend

A beautiful, modern Next.js frontend for the Web Search Agent API with AI-powered search and summarization.

## ✨ Features

- **Intelligent Search Interface**: Clean, intuitive search box with real-time feedback
- **Inspiring Loading Quotes**: Rotating inspirational quotes while searching
- **Dual Summary Modes**: Toggle between individual and combined summaries
- **Responsive Design**: Beautiful UI that works on all devices
- **Real-time Animations**: Smooth transitions and loading states
- **Error Handling**: Graceful error messages and fallbacks
- **Source Attribution**: Clear indication of successful vs failed scrapes

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🎯 Usage

### Basic Search

1. Enter your search query in the search box
2. Choose between "Combined Summary" or "Individual Summaries"
3. Click "Search" or press Enter
4. Enjoy the rotating quotes while the AI searches and analyzes content
5. View your results below the search box

### Summary Types

- **Combined Summary**: Get a single, comprehensive summary combining insights from all sources
- **Individual Summaries**: See separate summaries for each search result

### Example Queries

- "artificial intelligence trends 2024"
- "sustainable energy innovations"
- "React hooks tutorial"
- "quantum computing breakthroughs"

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **HTTP Client**: Axios

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with metadata
│   │   ├── page.tsx            # Main search interface
│   │   └── globals.css         # Global styles
│   └── components/
│       └── LoadingQuotes.tsx   # Loading quotes component
├── public/                     # Static assets
├── package.json               # Dependencies
└── README.md                  # This file
```

## 🎨 Design Features

### Visual Elements

- **Gradient Background**: Subtle blue-to-indigo gradient
- **Glass Morphism**: Modern frosted glass effects
- **Smooth Animations**: Page transitions and loading states
- **Responsive Layout**: Mobile-first design approach

### Interactive Elements

- **Search Box**: Large, prominent search input with icon
- **Toggle Buttons**: Easy switching between summary types
- **Loading States**: Animated quotes and progress indicators
- **Result Cards**: Clean, organized result presentation

### Color Scheme

- **Primary**: Indigo (600, 700)
- **Secondary**: Purple, Blue accents
- **Success**: Green (100, 800)
- **Error**: Red (100, 800)
- **Neutral**: Gray scale (50-800)

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file for custom configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Integration

The frontend expects the backend API to be running on `http://localhost:8000` with the following endpoints:

- `POST /search` - Individual summaries
- `POST /search/combined` - Combined summaries
- `GET /health` - Health check

## 📱 Responsive Design

The interface adapts to different screen sizes:

- **Desktop**: Full-width layout with side-by-side elements
- **Tablet**: Stacked layout with optimized spacing
- **Mobile**: Single-column layout with touch-friendly buttons

## 🎭 Loading Experience

### Inspirational Quotes

While searching, users see rotating quotes from famous thinkers:

- Albert Einstein
- Leonardo da Vinci
- Stephen Hawking
- And more...

### Visual Feedback

- Spinning icons
- Progress dots
- Smooth transitions
- Loading states

## 🚦 Error Handling

- **Network Errors**: Clear messages about backend connectivity
- **Invalid Queries**: Helpful feedback for unsupported queries
- **Timeout Handling**: Graceful handling of slow responses
- **Fallback States**: Always show something useful to the user

## 🔄 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Quality

- TypeScript for type safety
- ESLint for code quality
- Prettier for code formatting
- Tailwind CSS for consistent styling

## 🌟 Future Enhancements

- [ ] Dark mode toggle
- [ ] Search history
- [ ] Bookmarking results
- [ ] Export functionality
- [ ] Advanced search filters
- [ ] Real-time search suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Web Search Agent system. See the main project for licensing information.

---

**Powered by AI • Built with ❤️ using Next.js and Tailwind CSS**
