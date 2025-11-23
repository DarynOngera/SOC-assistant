# Threat Triage Actions - Current Status & Enhancements

## ✅ Currently Implemented

### Backend API Endpoints (server.py)

#### 1. **Escalate Alert** - `/api/alerts/<alert_id>/escalate`
**Features:**
- Escalate to Senior Analyst, SOC Manager, or Security Team Lead
- Optional priority increase (low→medium→high→critical)
- Escalation reason tracking
- Audit logging
- Real-time WebSocket notifications

**Request:**
```json
{
  "escalated_to": "Senior Analyst",
  "reason": "Complex attack pattern requires senior review",
  "priority_increase": true
}
```

#### 2. **Assign Alert** - `/api/alerts/<alert_id>/assign`
**Features:**
- Assign to specific analyst
- Assignment notes
- Notification to assigned analyst
- Audit logging
- Real-time updates

**Request:**
```json
{
  "assigned_to": "john_analyst",
  "notes": "Please investigate source IP and check for lateral movement"
}
```

#### 3. **Start Investigation** - `/api/alerts/<alert_id>/investigate`
**Features:**
- Mark alert as under investigation
- Set investigation priority (low/medium/high/urgent)
- Initial investigation notes
- Investigator tracking
- Audit logging

**Request:**
```json
{
  "priority": "high",
  "notes": "Investigating potential data exfiltration. Checking network logs."
}
```

#### 4. **Resolve Alert** - `/api/alerts/<alert_id>/resolve`
**Features:**
- Resolution types: resolved, false_positive, duplicate, no_action_required
- Required resolution notes
- Optional action taken documentation
- Audit logging
- Statistics update

**Request:**
```json
{
  "resolution_type": "false_positive",
  "notes": "Legitimate admin activity during maintenance window",
  "action_taken": "Added IP to whitelist"
}
```

#### 5. **Update Investigation** - `/api/alerts/<alert_id>/update-investigation`
**Features:**
- Add investigation notes
- Update investigation status
- Track investigation timeline
- Audit logging

**Request:**
```json
{
  "notes": "Found evidence of port scanning. Blocking source IP.",
  "status": "in_progress"
}
```

#### 6. **Flag Alert** - `/api/alerts/<alert_id>/flag`
**Features:**
- Mark alert for review
- Optional flag reason
- Quick attention marker

#### 7. **Dismiss Alert** - `/api/alerts/<alert_id>/dismiss`
**Features:**
- Dismiss non-critical alerts
- Optional dismiss reason
- Audit logging

#### 8. **Bulk Triage** - `/api/alerts/bulk-triage`
**Features:**
- Perform actions on multiple alerts
- Supported actions: flag, dismiss, assign
- Returns success/failure counts

**Request:**
```json
{
  "alert_ids": [123, 124, 125],
  "action": "assign",
  "action_data": {
    "assigned_to": "john_analyst"
  }
}
```

### Frontend Component (ThreatTriage.jsx)

**Features:**
- Priority-based alert filtering (high/medium/low)
- Alert selection with checkboxes
- Bulk action panel
- Individual action buttons per alert
- Modal forms for each action type
- Real-time updates (30s refresh)
- Priority score visualization
- Investigation status display

## 🎯 Recommended Enhancements

### 1. **Enhanced Investigation Workflow**

#### Add Investigation Timeline
```javascript
// Show investigation history
{
  "investigation_timeline": [
    {
      "timestamp": "2024-11-22T18:00:00Z",
      "analyst": "john_analyst",
      "action": "started_investigation",
      "notes": "Initial triage"
    },
    {
      "timestamp": "2024-11-22T18:15:00Z",
      "analyst": "john_analyst",
      "action": "updated",
      "notes": "Found suspicious activity"
    }
  ]
}
```

#### Add Evidence Collection
```javascript
// Attach evidence to alerts
{
  "evidence": [
    {
      "type": "pcap",
      "file": "suspicious_traffic.pcap",
      "uploaded_by": "john_analyst",
      "timestamp": "2024-11-22T18:20:00Z"
    },
    {
      "type": "screenshot",
      "file": "network_graph.png",
      "uploaded_by": "john_analyst"
    }
  ]
}
```

### 2. **Playbook Integration**

#### Automated Response Playbooks
```javascript
// Define playbooks for common attack types
{
  "playbooks": {
    "DDoS": {
      "steps": [
        "Identify source IPs",
        "Check rate limiting rules",
        "Block malicious IPs",
        "Monitor traffic patterns",
        "Document incident"
      ],
      "automated_actions": [
        "rate_limit_source",
        "notify_network_team"
      ]
    },
    "Port_Scan": {
      "steps": [
        "Identify scanner IP",
        "Check firewall logs",
        "Block source IP",
        "Check for successful connections"
      ]
    }
  }
}
```

### 3. **Collaboration Features**

#### Add Comments/Notes
```javascript
// Alert comments for team collaboration
{
  "comments": [
    {
      "id": 1,
      "analyst": "john_analyst",
      "timestamp": "2024-11-22T18:00:00Z",
      "comment": "Investigating source IP - appears to be compromised host",
      "mentions": ["@senior_analyst"]
    }
  ]
}
```

#### Add Alert Linking
```javascript
// Link related alerts
{
  "related_alerts": [123, 124, 125],
  "relationship_type": "same_attack_campaign"
}
```

### 4. **Enhanced Metrics & Reporting**

#### Analyst Performance Metrics
- Average time to triage
- Resolution rate
- False positive rate
- Escalation rate

#### Alert Lifecycle Tracking
- Time to first response
- Time to resolution
- Investigation duration
- Escalation path

### 5. **Smart Recommendations**

#### ML-Powered Suggestions
```javascript
{
  "recommendations": [
    {
      "type": "similar_alert",
      "message": "3 similar alerts resolved as false positives in the past week",
      "confidence": 0.85,
      "suggested_action": "mark_false_positive"
    },
    {
      "type": "pattern_detected",
      "message": "Part of coordinated attack from 5 source IPs",
      "suggested_action": "escalate"
    }
  ]
}
```

### 6. **Automated Actions**

#### Auto-Triage Rules
```javascript
{
  "auto_triage_rules": [
    {
      "condition": "severity == 'low' AND source_ip IN whitelist",
      "action": "auto_dismiss",
      "reason": "Whitelisted source"
    },
    {
      "condition": "attack_type == 'DDoS' AND anomaly_score > 0.9",
      "action": "auto_escalate",
      "escalate_to": "SOC Manager"
    }
  ]
}
```

### 7. **Enhanced UI Features**

#### Quick Actions Bar
- One-click common actions
- Keyboard shortcuts
- Drag-and-drop assignment

#### Alert Grouping
- Group by attack type
- Group by source IP
- Group by time window

#### Advanced Filtering
- Filter by analyst
- Filter by investigation status
- Filter by resolution type
- Date range filtering

## 🚀 Implementation Priority

### Phase 1: Essential Enhancements (Week 1)
1. ✅ Investigation timeline tracking
2. ✅ Enhanced comments/notes system
3. ✅ Alert linking for related incidents
4. ✅ Improved bulk actions

### Phase 2: Automation (Week 2)
1. ✅ Playbook integration
2. ✅ Auto-triage rules
3. ✅ Smart recommendations
4. ✅ Automated notifications

### Phase 3: Advanced Features (Week 3)
1. ✅ Evidence collection
2. ✅ Performance metrics
3. ✅ Advanced filtering
4. ✅ Alert grouping

## 📊 Current Workflow

```
Alert Generated → Triage Queue → Analyst Review → Action Taken
                                      ↓
                            [Escalate | Assign | Investigate | Resolve]
                                      ↓
                            Update Status & Notify
                                      ↓
                            Audit Log & Metrics
```

## 🎯 Enhanced Workflow (Proposed)

```
Alert Generated → Auto-Triage Rules → Smart Recommendations
                        ↓                      ↓
                  Triage Queue ← Playbook Suggestions
                        ↓
                 Analyst Review → Comments/Collaboration
                        ↓
              [Escalate | Assign | Investigate | Resolve]
                        ↓
              Evidence Collection & Timeline
                        ↓
              Update Status & Notify Team
                        ↓
              Audit Log, Metrics & Learning
```

## 📝 Next Steps

**What would you like to focus on?**

1. **Investigation Timeline** - Track investigation progress step-by-step
2. **Comments System** - Enable team collaboration on alerts
3. **Playbook Integration** - Guided response procedures
4. **Auto-Triage Rules** - Automated alert handling
5. **Evidence Collection** - Attach files and screenshots
6. **Performance Metrics** - Analyst and team performance tracking
7. **Smart Recommendations** - ML-powered triage suggestions

**Current Status:**
- ✅ All basic triage actions working
- ✅ Bulk operations functional
- ✅ Real-time updates via WebSocket
- ✅ Audit logging in place
- ✅ Frontend UI complete

**Ready to enhance!** Which feature should we implement first?
