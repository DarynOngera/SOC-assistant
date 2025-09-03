import React from 'react';
import { Activity, AlertTriangle, CheckCircle, TrendingUp, Shield, Zap } from 'lucide-react';

const StatusCards = ({ stats }) => {
  const cards = [
    {
      title: 'Total Processed',
      value: stats.total_processed?.toLocaleString() || '0',
      icon: Activity,
      color: 'text-primary-600',
      bgColor: 'bg-primary-50',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'Active Alerts',
      value: stats.active_alerts || '0',
      icon: AlertTriangle,
      color: 'text-danger-600',
      bgColor: 'bg-danger-50',
      change: stats.anomalies_detected > 0 ? `+${stats.anomalies_detected}` : '0',
      changeType: stats.anomalies_detected > 0 ? 'negative' : 'neutral'
    },
    {
      title: 'Detection Rate',
      value: `${stats.detection_rate || 0}%`,
      icon: TrendingUp,
      color: 'text-warning-600',
      bgColor: 'bg-warning-50',
      change: '+2.1%',
      changeType: 'positive'
    },
    {
      title: 'System Health',
      value: stats.system_health === 'healthy' ? 'Healthy' : 'Warning',
      icon: stats.system_health === 'healthy' ? CheckCircle : Shield,
      color: stats.system_health === 'healthy' ? 'text-success-600' : 'text-warning-600',
      bgColor: stats.system_health === 'healthy' ? 'bg-success-50' : 'bg-warning-50',
      change: 'Online',
      changeType: 'positive'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const IconComponent = card.icon;
        return (
          <div key={index} className="card hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className={`flex-shrink-0 ${card.bgColor} p-3 rounded-lg`}>
                <IconComponent className={`h-6 w-6 ${card.color}`} />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-500">{card.title}</p>
                <div className="flex items-baseline">
                  <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
                  <p className={`ml-2 text-sm font-medium ${
                    card.changeType === 'positive' ? 'text-success-600' :
                    card.changeType === 'negative' ? 'text-danger-600' : 'text-gray-500'
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
