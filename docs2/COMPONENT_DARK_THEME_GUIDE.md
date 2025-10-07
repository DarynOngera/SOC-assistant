# Component Dark Theme Update Guide

## Quick Find & Replace Patterns

Use these patterns to update all remaining components to the dark theme:

### 1. Background Colors

```javascript
// Find:
bg-white
// Replace with:
bg-slate-800/50 backdrop-blur-sm

// Find:
bg-gray-50
// Replace with:
bg-slate-900/50

// Find:
bg-gray-100
// Replace with:
bg-slate-700/50
```

### 2. Text Colors

```javascript
// Find:
text-gray-900
// Replace with:
text-white

// Find:
text-gray-700
// Replace with:
text-gray-300

// Find:
text-gray-600
// Replace with:
text-gray-400

// Find:
text-gray-500
// Replace with:
text-gray-400
```

### 3. Border Colors

```javascript
// Find:
border-gray-200
// Replace with:
border-slate-700/50

// Find:
border-gray-300
// Replace with:
border-slate-600/50
```

### 4. Hover States

```javascript
// Find:
hover:bg-gray-50
// Replace with:
hover:bg-slate-700/30

// Find:
hover:bg-gray-100
// Replace with:
hover:bg-slate-700/50
```

### 5. Input Fields

```javascript
// Find:
className="...border border-gray-300 rounded-md..."
// Replace with:
className="...bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400..."
```

### 6. Buttons

```javascript
// Find:
className="...bg-indigo-600 hover:bg-indigo-700..."
// Replace with:
className="...bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg shadow-blue-500/30..."
```

### 7. Cards

```javascript
// Find:
className="bg-white rounded-lg shadow..."
// Replace with:
className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50..."
```

### 8. Tables

```javascript
// Find:
className="bg-white divide-y divide-gray-200"
// Replace with:
className="bg-slate-800/30 divide-y divide-slate-700/50"

// Find:
className="bg-gray-50"  (for thead)
// Replace with:
className="bg-slate-900/50"
```

### 9. Badges

```javascript
// Find:
className="bg-blue-100 text-blue-800"
// Replace with:
className="bg-blue-600/20 text-blue-300 border border-blue-500/30"

// Find:
className="bg-green-100 text-green-800"
// Replace with:
className="bg-green-600/20 text-green-300 border border-green-500/30"

// Find:
className="bg-red-100 text-red-800"
// Replace with:
className="bg-red-600/20 text-red-300 border border-red-500/30"

// Find:
className="bg-yellow-100 text-yellow-800"
// Replace with:
className="bg-amber-600/20 text-amber-300 border border-amber-500/30"
```

## Component-Specific Updates

### AttackDistribution.jsx & AttackTrends.jsx

```javascript
// Update card wrapper
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <h3 className="text-lg font-semibold text-white mb-4">Title</h3>
  {/* Chart content */}
</div>
```

### ThreatTriage.jsx

```javascript
// Update main container
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <h2 className="text-xl font-bold text-white mb-4">Threat Triage</h2>
  {/* Content */}
</div>
```

### UserManagement.jsx

```javascript
// Update table and forms
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <table className="min-w-full divide-y divide-slate-700/50">
    <thead className="bg-slate-900/50">
      <tr>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
          Header
        </th>
      </tr>
    </thead>
    <tbody className="bg-slate-800/30 divide-y divide-slate-700/50">
      <tr className="hover:bg-slate-700/30">
        <td className="px-6 py-4 text-sm text-gray-300">
          Data
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### MFASetup.jsx

```javascript
// Update card
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <h3 className="text-lg font-semibold text-white mb-4">MFA Setup</h3>
  <p className="text-gray-300 mb-4">Description</p>
  {/* QR Code and form */}
</div>
```

### CSVAnalysis.jsx

```javascript
// Update upload area
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-6">
  <div className="border-2 border-dashed border-slate-600/50 rounded-lg p-8 text-center hover:border-blue-500/50 transition-colors">
    <p className="text-gray-300">Upload CSV</p>
  </div>
</div>
```

### AuditLogs.jsx

```javascript
// Update log entries
<div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-4">
  <div className="text-sm text-gray-300">
    Log entry
  </div>
</div>
```

## Automated Replacement Script

Run this in your terminal from the frontend directory:

```bash
# Find all component files with bg-white
find src/components -name "*.jsx" -o -name "*.js" | while read file; do
  # Backup
  cp "$file" "$file.bak"
  
  # Replace patterns
  sed -i 's/bg-white/bg-slate-800\/50 backdrop-blur-sm/g' "$file"
  sed -i 's/text-gray-900/text-white/g' "$file"
  sed -i 's/text-gray-700/text-gray-300/g' "$file"
  sed -i 's/text-gray-600/text-gray-400/g' "$file"
  sed -i 's/text-gray-500/text-gray-400/g' "$file"
  sed -i 's/border-gray-200/border-slate-700\/50/g' "$file"
  sed-i 's/border-gray-300/border-slate-600\/50/g' "$file"
  sed -i 's/bg-gray-50/bg-slate-900\/50/g' "$file"
  sed -i 's/bg-gray-100/bg-slate-700\/50/g' "$file"
  sed -i 's/hover:bg-gray-50/hover:bg-slate-700\/30/g' "$file"
  sed -i 's/hover:bg-gray-100/hover:bg-slate-700\/50/g' "$file"
  sed -i 's/divide-gray-200/divide-slate-700\/50/g' "$file"
  
  echo "Updated: $file"
done
```

## Manual Review Checklist

After automated replacement, manually review:

1. **Select dropdowns** - Ensure options are readable
2. **Modal backgrounds** - Add backdrop blur
3. **Chart text** - Update chart library text colors
4. **Icons** - Verify icon colors match theme
5. **Focus states** - Update focus ring colors to blue-500
6. **Disabled states** - Ensure disabled elements are visible
7. **Loading states** - Update spinner colors
8. **Tooltips** - Update tooltip backgrounds and text

## Testing Checklist

- [ ] All text is readable
- [ ] Buttons have proper hover states
- [ ] Forms are usable
- [ ] Tables display correctly
- [ ] Charts are visible
- [ ] Modals work properly
- [ ] Mobile view is functional
- [ ] Contrast ratios meet WCAG standards

## Common Issues & Fixes

### Issue: Select dropdown options are dark on dark
**Fix:**
```javascript
<select className="...">
  <option value="" className="bg-slate-800 text-white">Option</option>
</select>
```

### Issue: Chart text not visible
**Fix:** Update chart options:
```javascript
options={{
  plugins: {
    legend: {
      labels: {
        color: '#e2e8f0' // gray-200
      }
    }
  },
  scales: {
    x: {
      ticks: { color: '#cbd5e1' }, // gray-300
      grid: { color: 'rgba(148, 163, 184, 0.1)' }
    },
    y: {
      ticks: { color: '#cbd5e1' },
      grid: { color: 'rgba(148, 163, 184, 0.1)' }
    }
  }
}}
```

### Issue: Modal not visible
**Fix:**
```javascript
<div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50">
  <div className="bg-slate-800 border border-slate-700/50 rounded-lg p-6">
    {/* Content */}
  </div>
</div>
```

## Priority Components to Update

1. ✅ StatusCards.js - DONE
2. ✅ AlertsTable.js - DONE
3. ⏳ ThresholdControl.js
4. ⏳ ScoreDistribution.js
5. ⏳ AttackDistribution.jsx
6. ⏳ AttackTrends.jsx
7. ⏳ ThreatTriage.jsx
8. ⏳ UserManagement.jsx
9. ⏳ MFASetup.jsx
10. ⏳ AuditLogs.jsx
11. ⏳ CSVAnalysis.jsx
12. ⏳ NetworkMap.jsx

## Quick CSS Class Reference

```css
/* Backgrounds */
bg-slate-800/50 backdrop-blur-sm  /* Main card */
bg-slate-900/50                    /* Header/Footer */
bg-slate-700/50                    /* Input fields */
bg-slate-800/30                    /* Table body */

/* Text */
text-white          /* Headings */
text-gray-300       /* Body text */
text-gray-400       /* Muted text */

/* Borders */
border-slate-700/50  /* Main borders */
border-slate-600/50  /* Input borders */
border-blue-500/30   /* Accent borders */

/* Shadows */
shadow-xl                    /* Card shadow */
shadow-lg shadow-blue-500/30 /* Glow effect */

/* Hover */
hover:bg-slate-700/30  /* Subtle hover */
hover:bg-slate-700/50  /* Strong hover */
```

---

**Status:** In Progress  
**Updated:** 2025-09-30  
**Components Updated:** 2/12
