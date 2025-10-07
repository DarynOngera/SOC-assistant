# SOC Dashboard Design System

## 🎨 Color Palette

### Background Colors
```css
/* Main Background */
bg-gradient-to-br from-slate-900 via-blue-900/20 to-slate-900

/* Sidebar Background */
bg-gradient-to-b from-slate-900 to-slate-800

/* Card Background */
bg-slate-800/50 backdrop-blur-sm

/* Overlay Background */
bg-slate-900/50
```

### Text Colors
```css
/* Primary Text (Headings) */
text-white

/* Secondary Text (Body) */
text-gray-300

/* Muted Text (Labels) */
text-gray-400

/* Accent Text */
text-blue-300
text-cyan-300
```

### Border Colors
```css
/* Default Border */
border-slate-700/50

/* Accent Border */
border-blue-500/30
border-cyan-500/30

/* Success Border */
border-green-500/30

/* Danger Border */
border-red-500/30
```

### Gradient Colors
```css
/* Primary Gradient */
from-blue-600 to-cyan-600

/* Logo Badge */
from-blue-500 to-cyan-500

/* Hover State */
from-blue-700 to-cyan-700
```

## 🎯 Component Patterns

### Card Component
```jsx
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <h3 className="text-xl font-bold text-white mb-4">Title</h3>
  <p className="text-gray-300">Content</p>
</div>
```

### Primary Button
```jsx
<button className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg shadow-blue-500/30">
  Button Text
</button>
```

### Secondary Button
```jsx
<button className="bg-slate-700/50 text-gray-300 px-4 py-2 rounded-lg hover:bg-slate-600/50 hover:text-white transition-all duration-200 border border-slate-600/50">
  Button Text
</button>
```

### Success Button
```jsx
<button className="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg shadow-green-500/30 hover:bg-green-700 hover:shadow-green-500/50 transition-all duration-200 border border-green-500/30">
  Success Action
</button>
```

### Danger Button
```jsx
<button className="bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg shadow-red-500/30 hover:bg-red-700 hover:shadow-red-500/50 transition-all duration-200 border border-red-500/30">
  Danger Action
</button>
```

### Input Field
```jsx
<input 
  type="text"
  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
  placeholder="Enter text..."
/>
```

### Badge
```jsx
/* Info Badge */
<span className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded border border-blue-500/30">
  Info
</span>

/* Success Badge */
<span className="text-xs bg-green-600/20 text-green-300 px-2 py-1 rounded border border-green-500/30">
  Success
</span>

/* Warning Badge */
<span className="text-xs bg-amber-600/20 text-amber-300 px-2 py-1 rounded border border-amber-500/30">
  Warning
</span>

/* Danger Badge */
<span className="text-xs bg-red-600/20 text-red-300 px-2 py-1 rounded border border-red-500/30">
  Danger
</span>
```

### Alert Box
```jsx
/* Info Alert */
<div className="bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded">
  <p className="text-blue-300">Info message</p>
</div>

/* Success Alert */
<div className="bg-green-900/20 border-l-4 border-green-500 p-4 rounded">
  <p className="text-green-300">Success message</p>
</div>

/* Warning Alert */
<div className="bg-amber-900/20 border-l-4 border-amber-500 p-4 rounded">
  <p className="text-amber-300">Warning message</p>
</div>

/* Danger Alert */
<div className="bg-red-900/20 border-l-4 border-red-500 p-4 rounded">
  <p className="text-red-300">Error message</p>
</div>
```

### Navigation Item (Active)
```jsx
<button className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30">
  <Icon className="h-5 w-5 mr-3" />
  <span>Active Item</span>
</button>
```

### Navigation Item (Inactive)
```jsx
<button className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
  <Icon className="h-5 w-5 mr-3" />
  <span>Inactive Item</span>
</button>
```

### Status Indicator
```jsx
/* Online/Connected */
<div className="flex items-center">
  <div className="w-2 h-2 rounded-full bg-green-400 shadow-lg shadow-green-400/50 animate-pulse"></div>
  <span className="ml-2 text-sm text-gray-300">Connected</span>
</div>

/* Offline/Disconnected */
<div className="flex items-center">
  <div className="w-2 h-2 rounded-full bg-red-400 shadow-lg shadow-red-400/50 animate-pulse"></div>
  <span className="ml-2 text-sm text-gray-300">Disconnected</span>
</div>
```

### Modal/Dialog
```jsx
<div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
  <div className="bg-slate-800 border border-slate-700/50 rounded-lg shadow-2xl p-6 max-w-md w-full mx-4">
    <h3 className="text-xl font-bold text-white mb-4">Modal Title</h3>
    <p className="text-gray-300 mb-6">Modal content</p>
    <div className="flex justify-end space-x-3">
      <button className="px-4 py-2 bg-slate-700/50 text-gray-300 rounded-lg hover:bg-slate-600/50 transition-all duration-200">
        Cancel
      </button>
      <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg shadow-blue-500/30">
        Confirm
      </button>
    </div>
  </div>
</div>
```

### Table
```jsx
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 overflow-hidden">
  <table className="w-full">
    <thead className="bg-slate-900/50 border-b border-slate-700/50">
      <tr>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Header
        </th>
      </tr>
    </thead>
    <tbody className="divide-y divide-slate-700/50">
      <tr className="hover:bg-slate-700/30 transition-colors">
        <td className="px-6 py-4 text-sm text-gray-300">
          Data
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

## 📏 Spacing Scale

```css
/* Padding */
p-2   /* 8px */
p-3   /* 12px */
p-4   /* 16px */
p-6   /* 24px */
p-8   /* 32px */

/* Margin */
m-2   /* 8px */
m-3   /* 12px */
m-4   /* 16px */
m-6   /* 24px */
m-8   /* 32px */

/* Gap */
gap-2 /* 8px */
gap-3 /* 12px */
gap-4 /* 16px */
gap-6 /* 24px */
gap-8 /* 32px */
```

## 🔤 Typography Scale

```css
/* Headings */
text-3xl font-bold text-white  /* Page Title */
text-2xl font-bold text-white  /* Section Title */
text-xl font-semibold text-white  /* Card Title */
text-lg font-medium text-white  /* Subsection */

/* Body Text */
text-base text-gray-300  /* Normal */
text-sm text-gray-300    /* Small */
text-xs text-gray-400    /* Extra Small */
```

## 🎭 Shadow Scale

```css
/* Card Shadows */
shadow-xl  /* Large shadow */
shadow-2xl /* Extra large shadow */

/* Glow Shadows */
shadow-lg shadow-blue-500/30   /* Blue glow */
shadow-lg shadow-green-500/30  /* Green glow */
shadow-lg shadow-red-500/30    /* Red glow */
shadow-lg shadow-cyan-500/30   /* Cyan glow */
```

## 🔄 Animation Patterns

```css
/* Transitions */
transition-all duration-200  /* Standard transition */
transition-colors duration-200  /* Color only */
transition-transform duration-200  /* Transform only */

/* Hover Effects */
hover:scale-105  /* Slight grow */
hover:scale-95   /* Slight shrink */
active:scale-95  /* Click feedback */

/* Animations */
animate-pulse  /* Pulsing effect */
animate-spin   /* Spinning effect */
```

## 📐 Border Radius Scale

```css
rounded-sm   /* 2px */
rounded      /* 4px */
rounded-md   /* 6px */
rounded-lg   /* 8px */
rounded-xl   /* 12px */
rounded-full /* 9999px (circle) */
```

## 🎨 Glassmorphism Effect

```css
/* Standard Glassmorphism */
bg-slate-800/50 backdrop-blur-sm

/* Stronger Effect */
bg-slate-800/70 backdrop-blur-md

/* Lighter Effect */
bg-slate-800/30 backdrop-blur-sm
```

## 🌟 Icon Sizes

```css
h-4 w-4  /* 16px - Small icons */
h-5 w-5  /* 20px - Standard icons */
h-6 w-6  /* 24px - Medium icons */
h-8 w-8  /* 32px - Large icons */
h-10 w-10  /* 40px - Extra large icons */
```

## 📱 Responsive Breakpoints

```css
/* Mobile First */
sm:  /* 640px */
md:  /* 768px */
lg:  /* 1024px */
xl:  /* 1280px */
2xl: /* 1536px */
```

## ✨ Special Effects

### Glow on Hover
```css
hover:shadow-lg hover:shadow-blue-500/50
```

### Subtle Border Glow
```css
border border-blue-500/30 hover:border-blue-500/50
```

### Backdrop Blur
```css
backdrop-blur-sm  /* 4px blur */
backdrop-blur-md  /* 12px blur */
backdrop-blur-lg  /* 16px blur */
```

### Gradient Text
```css
bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent
```

## 🎯 Usage Guidelines

1. **Consistency:** Always use the defined patterns
2. **Contrast:** Ensure text is readable (WCAG AA minimum)
3. **Spacing:** Use the spacing scale for consistency
4. **Transitions:** Add smooth animations for better UX
5. **Responsiveness:** Test on multiple screen sizes
6. **Performance:** Use backdrop-blur sparingly
7. **Accessibility:** Maintain proper focus states

## 🚀 Quick Start

Copy and paste these patterns into your components. Adjust colors and spacing as needed while maintaining the overall aesthetic.

---

**Design System Version:** 1.0.0  
**Last Updated:** 2025-09-30  
**Theme:** Cybersecurity Dark
