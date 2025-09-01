import React, { useState } from 'react';
import { Sliders, Info } from 'lucide-react';

const ThresholdControl = ({ threshold, onThresholdChange }) => {
  const [localThreshold, setLocalThreshold] = useState(threshold);
  const [isAdjusting, setIsAdjusting] = useState(false);

  const handleSliderChange = (e) => {
    const newValue = parseFloat(e.target.value);
    setLocalThreshold(newValue);
    setIsAdjusting(true);
  };

  const handleSliderRelease = () => {
    if (isAdjusting) {
      onThresholdChange(localThreshold);
      setIsAdjusting(false);
    }
  };

  const getThresholdColor = (value) => {
    if (value >= 0.8) return 'text-danger-600';
    if (value >= 0.6) return 'text-warning-600';
    if (value >= 0.4) return 'text-yellow-600';
    return 'text-success-600';
  };

  const getThresholdBg = (value) => {
    if (value >= 0.8) return 'bg-danger-500';
    if (value >= 0.6) return 'bg-warning-500';
    if (value >= 0.4) return 'bg-yellow-500';
    return 'bg-success-500';
  };

  const getSensitivityLabel = (value) => {
    if (value >= 0.8) return 'Very Low Sensitivity';
    if (value >= 0.6) return 'Low Sensitivity';
    if (value >= 0.4) return 'Medium Sensitivity';
    if (value >= 0.2) return 'High Sensitivity';
    return 'Very High Sensitivity';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Sliders className="h-5 w-5 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">Detection Threshold</h3>
      </div>

      <div className="space-y-4">
        {/* Current Threshold Display */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Current Threshold:</span>
          <div className="flex items-center space-x-2">
            <span className={`text-2xl font-bold ${getThresholdColor(threshold)}`}>
              {threshold.toFixed(2)}
            </span>
            <span className={`text-sm px-2 py-1 rounded-full ${getThresholdColor(threshold)} bg-opacity-10`}>
              {getSensitivityLabel(threshold)}
            </span>
          </div>
        </div>

        {/* Threshold Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-500">
            <span>0.0</span>
            <span>0.5</span>
            <span>1.0</span>
          </div>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={localThreshold}
              onChange={handleSliderChange}
              onMouseUp={handleSliderRelease}
              onTouchEnd={handleSliderRelease}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #22c55e 0%, #f59e0b 50%, #ef4444 100%)`
              }}
            />
            <div
              className="absolute top-0 w-4 h-4 bg-white border-2 border-gray-400 rounded-full shadow-md transform -translate-y-1 cursor-pointer"
              style={{
                left: `calc(${localThreshold * 100}% - 8px)`,
                borderColor: getThresholdColor(localThreshold).includes('danger') ? '#ef4444' :
                           getThresholdColor(localThreshold).includes('warning') ? '#f59e0b' :
                           getThresholdColor(localThreshold).includes('yellow') ? '#eab308' : '#22c55e'
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>High Sensitivity</span>
            <span>Low Sensitivity</span>
          </div>
        </div>

        {/* Threshold Impact */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-gray-700">
              <p className="font-medium mb-1">Threshold Impact:</p>
              <ul className="space-y-1 text-xs">
                <li>• <strong>Lower values (0.0-0.4):</strong> More sensitive, catches more anomalies but may increase false positives</li>
                <li>• <strong>Higher values (0.6-1.0):</strong> Less sensitive, fewer false positives but may miss subtle anomalies</li>
                <li>• <strong>Recommended range:</strong> 0.4-0.7 for balanced detection</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="flex space-x-2">
          <button
            onClick={() => {
              setLocalThreshold(0.3);
              onThresholdChange(0.3);
            }}
            className="flex-1 px-3 py-2 text-xs bg-success-100 text-success-800 rounded-md hover:bg-success-200 transition-colors"
          >
            High Sensitivity
          </button>
          <button
            onClick={() => {
              setLocalThreshold(0.5);
              onThresholdChange(0.5);
            }}
            className="flex-1 px-3 py-2 text-xs bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 transition-colors"
          >
            Balanced
          </button>
          <button
            onClick={() => {
              setLocalThreshold(0.7);
              onThresholdChange(0.7);
            }}
            className="flex-1 px-3 py-2 text-xs bg-warning-100 text-warning-800 rounded-md hover:bg-warning-200 transition-colors"
          >
            Low Sensitivity
          </button>
        </div>
      </div>
    </div>
  );
};

export default ThresholdControl;
