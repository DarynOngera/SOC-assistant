# NLP Frontend Integration Guide

## Component Created

✅ **`frontend/src/components/NLPInsights.jsx`** - React component for displaying NLP analysis

## How to Integrate

### Option 1: Add to Alert Details Modal

```jsx
// In AlertsTable.js or wherever you show alert details

import NLPInsights from './NLPInsights';

// Inside your alert details modal/panel:
<div className="alert-details">
  {/* Existing alert information */}
  <div className="alert-info">
    <h3>Alert #{selectedAlert.id}</h3>
    <p>{selectedAlert.description}</p>
    {/* ... other alert fields ... */}
  </div>

  {/* NEW: Add NLP Insights */}
  <NLPInsights alert={selectedAlert} />
</div>
```

### Option 2: Add as Expandable Section in AlertsTable

```jsx
// In AlertsTable.js

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import NLPInsights from './NLPInsights';

const AlertRow = ({ alert }) => {
  const [showNLP, setShowNLP] = useState(false);

  return (
    <>
      <tr>
        <td>{alert.id}</td>
        <td>{alert.severity}</td>
        <td>{alert.description}</td>
        <td>
          <button
            onClick={() => setShowNLP(!showNLP)}
            className="text-blue-600 hover:text-blue-800"
          >
            {showNLP ? <ChevronUp /> : <ChevronDown />}
            NLP
          </button>
        </td>
      </tr>
      {showNLP && (
        <tr>
          <td colSpan="4" className="bg-gray-50 p-4">
            <NLPInsights alert={alert} />
          </td>
        </tr>
      )}
    </>
  );
};
```

### Option 3: Add to ThreatTriage Component

```jsx
// In ThreatTriage.jsx

import NLPInsights from './NLPInsights';

// When showing alert details:
<div className="threat-details">
  <h2>Alert Analysis</h2>
  
  {/* Existing threat triage info */}
  <div className="triage-info">
    {/* ... */}
  </div>

  {/* NEW: NLP Analysis */}
  <div className="mt-6">
    <NLPInsights alert={currentAlert} />
  </div>
</div>
```

## Features

The `NLPInsights` component automatically:

✅ **Checks NLP availability** - Shows graceful message if not available  
✅ **Analyzes alert text** - Calls `/api/nlp/analyze-alert`  
✅ **Enriches IP addresses** - Calls `/api/nlp/enrich-ip` if src_ip present  
✅ **Shows loading state** - Spinner while analyzing  
✅ **Error handling** - Shows error message if analysis fails  

## What It Displays

### NLP Analysis Section
- **Summary** - Human-readable alert summary
- **Severity** - Detected severity with color coding (Critical/High/Medium/Low)
- **Confidence Score** - Analysis confidence (0-100%)
- **Attack Types** - Detected attack patterns (SYN flood, port scan, etc.)
- **Extracted Entities** - IPs, ports, domains, CVEs, hashes
- **Security Keywords** - Important security-related terms

### Threat Intelligence Section
- **IP Address** - Source IP being analyzed
- **Reputation Score** - 0-100 (higher = more malicious)
- **Status** - Malicious or Clean with icon
- **Threat Categories** - Malware, botnet, scanning, etc.
- **Geolocation** - Country and city

## Styling

The component uses Tailwind CSS classes and matches your existing design:
- Color-coded severity badges
- Progress bars for scores
- Clean card layout
- Responsive grid
- Icons from lucide-react

## Example Usage

```jsx
import NLPInsights from './components/NLPInsights';

function AlertDetailsPage() {
  const alert = {
    id: 123,
    description: "SYN flood attack detected from 192.168.1.100",
    src_ip: "192.168.1.100",
    attack_type: "syn_flood",
    severity: "high"
  };

  return (
    <div className="container mx-auto p-6">
      <h1>Alert Details</h1>
      
      {/* Show NLP insights */}
      <NLPInsights alert={alert} />
    </div>
  );
}
```

## API Endpoints Used

The component calls these endpoints (already implemented in server.py):

1. **`GET /api/nlp/status`** - Check if NLP is available
2. **`POST /api/nlp/analyze-alert`** - Analyze alert text
3. **`POST /api/nlp/enrich-ip`** - Get threat intelligence for IP

## Testing

1. **Start the backend:**
   ```bash
   cd /home/ongera/projects/SOC-assistant
   source venv/bin/activate
   python src/dashboard/server.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **View an alert** - The NLP insights will automatically load

## Customization

### Change Colors

```jsx
// In NLPInsights.jsx, modify getSeverityColor():
const getSeverityColor = (severity) => {
  const colors = {
    critical: 'bg-red-100 text-red-800 border-red-300',  // Change these
    high: 'bg-orange-100 text-orange-800 border-orange-300',
    // ...
  };
  return colors[severity] || colors.unknown;
};
```

### Hide Sections

```jsx
// Don't show threat intelligence:
{threatIntel?.success && false && (
  <div>...</div>
)}
```

### Add Custom Fields

```jsx
// Add new field to display:
<div>
  <label>Custom Field</label>
  <span>{nlpAnalysis.analysis?.custom_field}</span>
</div>
```

## Screenshots

### NLP Analysis Card
```
┌─────────────────────────────────────────────────┐
│ 🧠 NLP Analysis                                 │
├─────────────────────────────────────────────────┤
│ [MEDIUM] | Detected: syn_flood | IPs: 192...   │
│                                                 │
│ Detected Severity: [MEDIUM]  Confidence: 85%   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                 │
│ Attack Types: [syn_flood]                       │
│ Entities: IP: 192.168.1.100  Port: 80          │
└─────────────────────────────────────────────────┘
```

### Threat Intelligence Card
```
┌─────────────────────────────────────────────────┐
│ 🛡️ Threat Intelligence                          │
├─────────────────────────────────────────────────┤
│ ⚠️ 192.168.1.100 - Low Risk (Score: 10/100)    │
│                                                 │
│ IP: 192.168.1.100          Score: 10/100       │
│ Status: ✓ Clean                                 │
│ Location: Internal Network, Local               │
└─────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Import `NLPInsights` component
2. ✅ Add to alert details view
3. ✅ Test with real alerts
4. ⏭️ Customize styling to match your theme
5. ⏭️ Add to other views (Threat Triage, Attack Distribution, etc.)

## Troubleshooting

### "NLP analysis not available"
- Check backend is running
- Verify `/api/nlp/status` returns `nlp_available: true`
- Check browser console for errors

### No data showing
- Ensure alert has `description` or `text` field
- Check Network tab for API call responses
- Verify token is valid in localStorage

### Styling issues
- Make sure Tailwind CSS is configured
- Import lucide-react icons: `npm install lucide-react`
- Check for CSS conflicts

---

**The NLP frontend component is ready to use!** 🎯
