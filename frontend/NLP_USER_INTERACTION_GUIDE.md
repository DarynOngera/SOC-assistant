# NLP User Interaction Points

## Where Users See NLP Insights

The `NLPInsights` component can be integrated in **3 main places** where users interact with alerts:

---

## 1. Alert Details Modal (Recommended) ⭐

**Location:** When user clicks on an alert to view details

**File to Modify:** `src/components/ThreatTriage.jsx`

### Implementation:

```jsx
// At the top of ThreatTriage.jsx
import NLPInsights from './NLPInsights';

// Inside the TriageModal component, add NLP section:
const TriageModal = () => {
  // ... existing code ...

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-6 border w-full max-w-4xl shadow-lg rounded-md bg-slate-800/50 backdrop-blur-sm">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white capitalize">
              {triageAction} Alert #{currentAlert.id}
            </h3>
            <button onClick={() => setShowTriageModal(false)}>
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Alert Details */}
          <div className="mb-6 p-4 bg-slate-700/30 rounded-lg">
            <h4 className="text-sm font-medium text-gray-300 mb-2">Alert Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Source IP:</span>
                <span className="text-white ml-2">{currentAlert.source_ip}</span>
              </div>
              <div>
                <span className="text-gray-400">Attack Type:</span>
                <span className="text-white ml-2">{currentAlert.attack_type}</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-400">Description:</span>
                <p className="text-white mt-1">{currentAlert.description || 'No description'}</p>
              </div>
            </div>
          </div>

          {/* 🎯 NLP INSIGHTS - NEW SECTION */}
          <div className="mb-6">
            <NLPInsights alert={currentAlert} />
          </div>

          {/* Existing triage form */}
          <form onSubmit={handleSubmit}>
            {renderModalContent()}
            {/* ... rest of form ... */}
          </form>
        </div>
      </div>
    </div>
  );
};
```

**User Experience:**
1. User clicks "Escalate", "Assign", or "Investigate" on an alert
2. Modal opens showing alert details
3. **NLP Insights automatically appear** below alert info
4. User sees:
   - Severity classification
   - Attack types detected
   - Extracted entities (IPs, CVEs, etc.)
   - Threat intelligence for source IP
5. User makes informed decision based on NLP analysis

---

## 2. Expandable Row in Alerts Table

**Location:** Directly in the alerts table

**File to Modify:** `src/components/AlertsTable.js`

### Implementation:

```jsx
// At the top
import { ChevronDown, ChevronUp, Brain } from 'lucide-react';
import NLPInsights from './NLPInsights';

const AlertsTable = ({ alerts, onAlertAction }) => {
  const [expandedAlert, setExpandedAlert] = useState(null);

  // ... existing code ...

  return (
    <div className="space-y-4">
      {/* ... filters ... */}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead>
            {/* ... existing headers ... */}
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
              NLP
            </th>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {paginatedAlerts.map((alert) => (
              <React.Fragment key={alert.id}>
                {/* Main Row */}
                <tr className="hover:bg-slate-700/30">
                  {/* ... existing columns ... */}
                  
                  {/* NLP Toggle Column */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => setExpandedAlert(
                        expandedAlert === alert.id ? null : alert.id
                      )}
                      className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <Brain className="h-4 w-4" />
                      {expandedAlert === alert.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  </td>
                </tr>

                {/* 🎯 Expanded NLP Row */}
                {expandedAlert === alert.id && (
                  <tr>
                    <td colSpan="8" className="px-6 py-4 bg-slate-800/50">
                      <NLPInsights alert={alert} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

**User Experience:**
1. User sees alerts in table
2. User clicks 🧠 icon in "NLP" column
3. **Row expands** to show NLP insights
4. User can expand multiple alerts to compare
5. Click again to collapse

---

## 3. Dedicated NLP Analysis Tab

**Location:** New tab in the main dashboard

**File to Create:** `src/components/NLPAnalysis.jsx`

### Implementation:

```jsx
import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, Shield, AlertTriangle } from 'lucide-react';
import NLPInsights from './NLPInsights';

const NLPAnalysis = () => {
  const [alerts, setAlerts] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [nlpStats, setNlpStats] = useState(null);

  useEffect(() => {
    fetchAlerts();
    fetchNLPStats();
  }, []);

  const fetchAlerts = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/alerts?limit=50', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setAlerts(data.alerts || []);
    if (data.alerts?.length > 0) {
      setSelectedAlert(data.alerts[0]);
    }
  };

  const fetchNLPStats = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/nlp/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setNlpStats(data);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Brain className="h-8 w-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">NLP Analysis</h1>
            <p className="text-gray-400">AI-powered alert intelligence</p>
          </div>
        </div>
        {nlpStats?.nlp_available && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-medium">NLP Active</span>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="text-gray-400 text-sm">Critical Alerts</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {alerts.filter(a => a.severity === 'critical').length}
          </div>
        </div>
        {/* Add more stat cards */}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert List */}
        <div className="lg:col-span-1 bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Alerts</h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {alerts.map(alert => (
              <button
                key={alert.id}
                onClick={() => setSelectedAlert(alert)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedAlert?.id === alert.id
                    ? 'bg-blue-500/20 border border-blue-500/30'
                    : 'bg-slate-700/30 hover:bg-slate-700/50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-medium">#{alert.id}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    alert.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                    alert.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-400 truncate">{alert.attack_type}</p>
              </button>
            ))}
          </div>
        </div>

        {/* 🎯 NLP Insights Panel */}
        <div className="lg:col-span-2">
          {selectedAlert ? (
            <NLPInsights alert={selectedAlert} />
          ) : (
            <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-12 text-center">
              <Brain className="h-16 w-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Select an alert to view NLP analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NLPAnalysis;
```

**Add to App.js:**

```jsx
import NLPAnalysis from './components/NLPAnalysis';

// In the navigation/routing:
<Route path="/nlp-analysis" element={<NLPAnalysis />} />

// Add to sidebar:
<NavLink to="/nlp-analysis">
  <Brain className="h-5 w-5" />
  <span>NLP Analysis</span>
</NavLink>
```

**User Experience:**
1. User clicks "NLP Analysis" in sidebar
2. Sees dedicated page with:
   - List of recent alerts
   - NLP insights for selected alert
   - Statistics dashboard
3. Can browse through alerts and see instant NLP analysis

---

## Recommended Integration Strategy

### Phase 1: Quick Win (5 minutes)
✅ **Add to ThreatTriage modal** - Users already interact with modals for alert actions

### Phase 2: Enhanced UX (15 minutes)
✅ **Add expandable rows in AlertsTable** - Quick access without leaving the table

### Phase 3: Advanced (30 minutes)
✅ **Create dedicated NLP Analysis tab** - Power users can deep-dive into NLP insights

---

## Visual Flow Diagram

```
User Journey with NLP:

1. Dashboard → Alerts Table
   ↓
2. Click Alert → Modal Opens
   ↓
3. See Alert Details
   ↓
4. 🎯 NLP Insights Auto-Load
   ├─ Severity: [CRITICAL]
   ├─ Attack Types: [syn_flood, malware]
   ├─ Entities: IPs, CVEs, Domains
   └─ Threat Intel: IP Reputation
   ↓
5. User Makes Informed Decision
   ├─ Escalate (with NLP context)
   ├─ Assign (with threat intel)
   └─ Investigate (with entity info)
```

---

## Quick Start: Add to ThreatTriage (5 minutes)

1. **Open:** `frontend/src/components/ThreatTriage.jsx`

2. **Add import** at top:
```jsx
import NLPInsights from './NLPInsights';
```

3. **Find the TriageModal** component (around line 276)

4. **Add NLP section** after alert details, before the form:
```jsx
{/* NLP Insights */}
<div className="mb-6">
  <NLPInsights alert={currentAlert} />
</div>
```

5. **Save and test!**

---

## Testing

1. Start backend:
```bash
source venv/bin/activate
python src/dashboard/server.py
```

2. Start frontend:
```bash
cd frontend
npm start
```

3. Navigate to Threat Triage

4. Click "Escalate" or "Investigate" on any alert

5. **NLP insights will automatically appear!**

---

## Customization

### Hide Specific Sections

```jsx
<NLPInsights 
  alert={alert}
  showThreatIntel={false}  // Hide threat intelligence
/>
```

### Custom Styling

```jsx
<div className="my-custom-wrapper">
  <NLPInsights alert={alert} />
</div>
```

### Loading State

The component handles its own loading state automatically!

---

## Summary

**Users interact with NLP in 3 places:**

1. ⭐ **Alert Details Modal** (ThreatTriage) - **Recommended first**
2. 📊 **Expandable Table Rows** (AlertsTable) - Quick access
3. 🧠 **Dedicated NLP Tab** - Deep analysis

**Easiest integration:** Add 3 lines to `ThreatTriage.jsx` ✅

**Your users will see NLP insights automatically when viewing alert details!** 🎯
