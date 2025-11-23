# Quick Reference: PCAP Replay Testing

## 🚀 Start System

```bash
# Terminal 1: Backend
cd /home/ongera/projects/SOC-assistant/src/dashboard
python3 server.py

# Terminal 2: Frontend
cd /home/ongera/projects/SOC-assistant/frontend
npm start
```

## 🧪 Test Normal Traffic

1. Login → Mininet Simulation
2. Settings → Mode: **Normal Traffic**
3. Click **Start Simulation**
4. **Expected:** 0-10 alerts, Healthy status

## ⚔️ Test Attack Traffic

1. Settings → Mode: **Attack Simulation**
2. Attack Type: **SYN Flood** (or any other)
3. Click **Start Simulation**
4. **Expected:** 50-200 alerts, Critical status

## 📊 Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | 95.25% |
| Precision | 98.84% |
| Recall | 95.53% |
| F1 Score | 97.16% |

## 🎯 Key Differences

| | Normal | Attack |
|-|--------|--------|
| **Alerts** | 0-10 | 50-200 |
| **Health** | 🟢 Healthy | 🔴 Critical |
| **Scores** | < 0.5 | > 0.7 |

## 📁 Important Files

```
models/mininet_model.pkl          ← Trained model
training_reports/*.png            ← Visualizations
mininet_data_generation/.../pcaps ← PCAP files
```

## 🔄 Regenerate Everything

```bash
# 1. Generate new PCAPs
python3 generate_varied_pcaps.py

# 2. Train new model
python3 train_comprehensive_model.py

# 3. Restart dashboard
cd src/dashboard && python3 server.py
```

## 📖 Full Guides

- **Testing:** `PCAP_REPLAY_TESTING_GUIDE.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`

---

**Ready to test! 🎉**
