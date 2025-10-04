# Quote Component

A beautiful, responsive React component that fetches and displays motivational quotes from an external API with elegant loading and error states.

## Features

- 🔄 **Real-time quote fetching** from backend API (`/external/quote`)
- 🎨 **Modern, responsive design** with smooth animations
- ⏱️ **Auto-refresh functionality** with configurable intervals
- 🔄 **Manual refresh** with animated loading states
- 📱 **Mobile-friendly** responsive layout
- 🎯 **Graceful error handling** with retry functionality
- ✨ **Beautiful animations** using Framer Motion
- 🏷️ **Tag display** for quote categories
- 📊 **Source tracking** (API vs fallback quotes)
- ⏰ **Timestamp display** showing when quote was fetched

## Usage

### Basic Implementation

```jsx
import Quote from '../components/Quote';

function App() {
  return (
    <div>
      <Quote />
    </div>
  );
}
```

### With Auto-refresh

```jsx
<Quote 
  autoRefresh={true} 
  refreshInterval={60000} // Refresh every minute
  className="mb-6"
/>
```

### Custom Styling

```jsx
<Quote 
  className="w-full max-w-2xl mx-auto border-2 border-blue-200"
  autoRefresh={false}
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes |
| `autoRefresh` | `boolean` | `false` | Enable automatic quote refresh |
| `refreshInterval` | `number` | `30000` | Auto-refresh interval in milliseconds |

## API Integration

The component integrates with the backend API endpoint:

- **Endpoint**: `GET /external/quote`
- **Query Parameters**: 
  - `use_fallback` (boolean): Whether to use fallback quotes if external API fails

### Expected API Response

```json
{
  "content": "The only way to do great work is to love what you do.",
  "author": "Steve Jobs",
  "tags": ["motivational", "work"],
  "length": 52,
  "source": "quotable.io",
  "fallback_reason": null
}
```

## Component States

### Loading State
- Shows animated spinner
- Displays "Loading inspiration..." message
- Smooth fade-in animation

### Error State
- Shows error icon and message
- Provides "Try Again" button
- Handles network errors gracefully

### Success State
- Displays quote with beautiful typography
- Shows author attribution
- Displays relevant tags
- Shows source and timestamp information

## Styling

The component uses:
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Heroicons** for icons
- **Gradient backgrounds** for visual appeal
- **Responsive design** that works on all screen sizes

## Dependencies

- React 18+
- Framer Motion
- Heroicons
- React Hot Toast (for notifications)
- Your API service (assumed to be in `../services/api`)

## Error Handling

- **Network errors**: Shows user-friendly error message with retry option
- **API failures**: Handles fallback quotes gracefully
- **Loading states**: Prevents multiple simultaneous requests
- **Toast notifications**: Shows fallback notifications when applicable

## Accessibility

- Semantic HTML structure
- Proper ARIA labels
- Keyboard navigation support
- Screen reader friendly
- High contrast colors

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- **Efficient re-renders** with React hooks
- **Automatic cleanup** of intervals
- **Error boundaries** prevent crashes
- **Optimized animations** with Framer Motion

## Customization

### Colors
The component uses a purple/indigo color scheme that can be customized by modifying the Tailwind classes:

```jsx
// Change to blue theme
<Quote className="bg-gradient-to-br from-blue-50 to-cyan-50" />
```

### Typography
Quote text styling can be customized:

```css
.quote-text {
  @apply text-xl font-serif italic;
}
```

### Animation Speed
Modify animation durations in the component:

```jsx
// Slower animations
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.8 }}
>
```

## Examples

### Integration in Dashboard

```jsx
function Dashboard() {
  return (
    <div className="dashboard">
      <Header />
      
      {/* Inspiration section */}
      <Quote 
        className="mb-6" 
        autoRefresh={true} 
        refreshInterval={300000} // 5 minutes
      />
      
      <MainContent />
    </div>
  );
}
```

### Sidebar Widget

```jsx
function Sidebar() {
  return (
    <aside className="sidebar">
      <Navigation />
      
      {/* Daily inspiration */}
      <Quote 
        className="mt-4 text-sm" 
        autoRefresh={true}
        refreshInterval={86400000} // Once per day
      />
    </aside>
  );
}
```

## Development

### Running Tests

```bash
npm test Quote.test.jsx
```

### Building for Production

The component is optimized for production builds with:
- Tree shaking support
- Minimal bundle size
- Optimized animations

---

## Contributing

When contributing to this component:

1. Maintain the existing API interface
2. Add proper TypeScript types if migrating
3. Update this README with new features
4. Test on multiple screen sizes
5. Ensure accessibility compliance