import React from 'react';
import { Activity, AlertTriangle, CheckCircle, TrendingUp, Shield, Zap } from 'lucide-react';

const StatusCards = ({ stats }) => {
  const cards = [
    {
      title: 'Total Processed',
      value: stats.total_processed?.toLocaleString() || '0',
      icon: Activity,
      color: 'text-blue-400',
      bgColor: 'bg-blue-600/20',
      borderColor: 'border-blue-500/30',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'Active Alerts',
      value: stats.active_alerts || '0',
      icon: AlertTriangle,
      color: 'text-red-400',
      bgColor: 'bg-red-600/20',
      borderColor: 'border-red-500/30',
      change: stats.anomalies_detected > 0 ? `+${stats.anomalies_detected}` : '0',
      changeType: stats.anomalies_detected > 0 ? 'negative' : 'neutral'
    },
    {
      title: 'Detection Rate',
      value: `${stats.detection_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-600/20',
      borderColor: 'border-cyan-500/30',
      change: '+2.1%',
      changeType: 'positive'
    },
    {
      title: 'System Health',
      value: stats.system_health === 'healthy' ? 'Healthy' : 'Warning',
      icon: stats.system_health === 'healthy' ? CheckCircle : Shield,
      color: stats.system_health === 'healthy' ? 'text-green-400' : 'text-amber-400',
      bgColor: stats.system_health === 'healthy' ? 'bg-green-600/20' : 'bg-amber-600/20',
      borderColor: stats.system_health === 'healthy' ? 'border-green-500/30' : 'border-amber-500/30',
      change: 'Online',
      changeType: 'positive'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const IconComponent = card.icon;
        return (
          <div key={index} className="card hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-200">
            <div className="flex items-center">
              <div className={`flex-shrink-0 ${card.bgColor} p-3 rounded-lg border ${card.borderColor}`}>
                <IconComponent className={`h-6 w-6 ${card.color}`} />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-400">{card.title}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-white">{card.value}</p>
                  <p className={`ml-2 text-sm font-medium ${
                    card.changeType === 'positive' ? 'text-green-400' :
                    card.changeType === 'negative' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {card.change}
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatusCards;
