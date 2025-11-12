import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw } from 'lucide-react';

const NetworkMap = () => {
  // eslint-disable-next-line no-unused-vars
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [], subnets: [], stats: {} });
  const [mininetTopology, setMininetTopology] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [timeframe] = useState('1h');
  const [filterType, setFilterType] = useState('all');
  const [maxNodes, setMaxNodes] = useState(20);
  const [showLabels, setShowLabels] = useState(false);
  const [showSubnets, setShowSubnets] = useState(true);
  const [viewMode, setViewMode] = useState('mininet'); // 'mininet' or 'alerts'
  const svgRef = useRef(null);

  useEffect(() => {
    fetchNetworkData();
    fetchMininetTopology();
    fetchConnections();
    const interval = setInterval(() => {
      fetchNetworkData();
      fetchMininetTopology();
      fetchConnections();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeframe]);

  const fetchNetworkData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/network/topology', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setNetworkData(data);
      }
    } catch (error) {
      console.error('Error fetching network data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMininetTopology = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:5000/api/network/mininet-topology', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.available) {
          setMininetTopology(data);
          console.log('Mininet topology loaded:', data.hosts?.length || 0, 'hosts');
        } else {
          console.log('Mininet topology not available:', data.message);
        }
      }
    } catch (error) {
      console.error('Error fetching Mininet topology:', error);
    }
  };

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:5000/api/network/connections?timeframe=${timeframe}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // connections data processed but not stored in state for demo
        console.log('Connections fetched:', data.connections?.length || 0);
      }
    } catch (error) {
      console.error('Error fetching connections:', error);
    }
  };

  const getNodeColor = (node) => {
    if (node.type === 'external') return '#ef4444'; // Red for external
    if (node.type === 'internal') return '#3b82f6'; // Blue for internal
    if (node.type === 'localhost') return '#10b981'; // Green for localhost
    return '#6b7280'; // Gray for unknown
  };

  const getNodeSize = (node) => {
    const baseSize = 25; // Much larger for demo
    const alertMultiplier = Math.min(node.alert_count / 30, 1.5);
    return baseSize + (alertMultiplier * 10);
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#d97706';
      case 'low': return '#65a30d';
      default: return '#6b7280';
    }
  };

  // Aggregate nodes by subnet to reduce density (unused in demo)
  /*
  const aggregateNodesBySubnet = (nodes) => {
    const subnets = {};
    
    nodes.forEach(node => {
      const segment = getSegmentFromIP(node.id);
      const subnetKey = `${segment}_${node.subnet}`;
      
      if (!subnets[subnetKey]) {
        subnets[subnetKey] = {
          id: subnetKey,
          segment,
          subnet: node.subnet,
          type: node.type,
          nodes: [],
          alert_count: 0,
          severity_counts: { critical: 0, high: 0, medium: 0, low: 0 },
          representative_ip: node.id
        };
      }
      
      subnets[subnetKey].nodes.push(node);
      subnets[subnetKey].alert_count += node.alert_count || 0;
      
      Object.keys(node.severity_counts || {}).forEach(severity => {
        subnets[subnetKey].severity_counts[severity] += node.severity_counts[severity] || 0;
      });
    });
    
    return Object.values(subnets);
  };
  */
  
  // eslint-disable-next-line no-unused-vars
  const getSegmentFromIP = (ip) => {
    if (ip.startsWith('10.1.0.')) return 'dmz';
    if (ip.startsWith('192.168.1.')) return 'internal';
    if (ip.startsWith('10.0.1.')) return 'servers';
    if (ip.startsWith('172.16.1.')) return 'management';
    if (ip.startsWith('192.168.100.')) return 'guest';
    return 'external';
  };

  /*
  const baseFilteredNodes = networkData.nodes.filter(node => {
    if (filterType === 'all') return true;
    if (filterType === 'internal') return node.type === 'internal';
    if (filterType === 'external') return node.type === 'external';
    if (filterType === 'high-risk') return node.alert_count > 5;
    return true;
  });
  */
  
  // Create demo topology with fixed key nodes for clarity
  const createDemoTopology = () => {
    return [
      {
        id: 'internet',
        segment: 'external',
        type: 'external',
        alert_count: 45,
        subnet: 'Internet',
        representative_ip: '203.0.113.1',
        nodes: [{id: '203.0.113.1'}, {id: '185.220.100.5'}, {id: '91.219.236.8'}],
        severity_counts: { critical: 15, high: 20, medium: 10, low: 0 }
      },
      {
        id: 'firewall',
        segment: 'dmz',
        type: 'internal',
        alert_count: 12,
        subnet: '10.1.0.0/24',
        representative_ip: '10.1.0.1',
        nodes: [{id: '10.1.0.1'}],
        severity_counts: { critical: 2, high: 5, medium: 5, low: 0 }
      },
      {
        id: 'web_servers',
        segment: 'dmz',
        type: 'internal',
        alert_count: 28,
        subnet: '10.1.0.0/24',
        representative_ip: '10.1.0.10',
        nodes: [{id: '10.1.0.10'}, {id: '10.1.0.11'}, {id: '10.1.0.12'}],
        severity_counts: { critical: 8, high: 12, medium: 8, low: 0 }
      },
      {
        id: 'internal_network',
        segment: 'internal',
        type: 'internal',
        alert_count: 18,
        subnet: '192.168.1.0/24',
        representative_ip: '192.168.1.50',
        nodes: [{id: '192.168.1.50'}, {id: '192.168.1.51'}, {id: '192.168.1.52'}],
        severity_counts: { critical: 3, high: 8, medium: 7, low: 0 }
      },
      {
        id: 'database_servers',
        segment: 'servers',
        type: 'internal',
        alert_count: 22,
        subnet: '10.0.1.0/24',
        representative_ip: '10.0.1.10',
        nodes: [{id: '10.0.1.10'}, {id: '10.0.1.11'}],
        severity_counts: { critical: 5, high: 10, medium: 7, low: 0 }
      },
      {
        id: 'management',
        segment: 'management',
        type: 'internal',
        alert_count: 8,
        subnet: '172.16.1.0/24',
        representative_ip: '172.16.1.10',
        nodes: [{id: '172.16.1.10'}],
        severity_counts: { critical: 1, high: 3, medium: 4, low: 0 }
      }
    ];
  };
  
  // Use demo topology for clear visualization
  const filteredNodes = createDemoTopology();

  const MininetVisualization = () => {
    if (!mininetTopology || !mininetTopology.available) {
      return (
        <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
          <div className="text-center">
            <p className="text-gray-400 mb-4">Mininet topology not available</p>
            <p className="text-sm text-gray-500">Run topology_exporter.py to generate topology data</p>
          </div>
        </div>
      );
    }

    const width = 1000;
    const height = 700;
    
    const hosts = mininetTopology.hosts || [];
    const switches = mininetTopology.switches || [];
    const links = mininetTopology.links || [];
    const segments = mininetTopology.segments || [];
    
    // Get segment colors
    const segmentColors = {};
    segments.forEach(seg => {
      segmentColors[seg.id] = seg.color;
    });
    
    const getHostColor = (host) => {
      if (host.alert_count > 10) return '#dc2626'; // Critical
      if (host.alert_count > 5) return '#ea580c'; // High
      if (host.alert_count > 0) return '#d97706'; // Medium
      return segmentColors[host.segment] || '#6b7280';
    };
    
    const getHostSize = (host) => {
      const baseSize = host.type === 'server' ? 20 : 15;
      const alertMultiplier = Math.min(host.alert_count / 20, 1.5);
      return baseSize + (alertMultiplier * 8);
    };

    return (
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <div className="w-full overflow-x-auto">
          <svg 
            ref={svgRef} 
            width={Math.max(width, 800)} 
            height={Math.max(height, 500)} 
            className="border border-gray-700 min-w-full"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Background grid */}
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Network Segments */}
            {showSubnets && segments.map((segment, idx) => {
              const segmentHosts = hosts.filter(h => h.segment === segment.id);
              if (segmentHosts.length === 0) return null;
              
              const xs = segmentHosts.map(h => h.position.x);
              const ys = segmentHosts.map(h => h.position.y);
              const minX = Math.min(...xs) - 80;
              const maxX = Math.max(...xs) + 80;
              const minY = Math.min(...ys) - 60;
              const maxY = Math.max(...ys) + 60;
              
              return (
                <g key={`segment-${idx}`}>
                  <rect 
                    x={minX} 
                    y={minY} 
                    width={maxX - minX} 
                    height={maxY - minY} 
                    fill={`${segment.color}20`} 
                    stroke={segment.color} 
                    strokeWidth="2" 
                    rx="10" 
                  />
                  <text 
                    x={minX + 10} 
                    y={minY + 25} 
                    className="fill-white text-sm font-bold"
                  >
                    {segment.name.toUpperCase()}
                  </text>
                  <text 
                    x={minX + 10} 
                    y={minY + 42} 
                    className="fill-gray-300 text-xs"
                  >
                    {segment.subnet}
                  </text>
                </g>
              );
            })}
            
            {/* Links */}
            {links.map((link, idx) => {
              const sourceNode = [...hosts, ...switches].find(n => n.id === link.source);
              const targetNode = [...hosts, ...switches].find(n => n.id === link.target);
              
              if (!sourceNode || !targetNode) return null;
              
              const linkColor = link.type === 'trunk' ? '#fbbf24' : '#6b7280';
              const linkWidth = link.type === 'trunk' ? 3 : 1.5;
              
              return (
                <line
                  key={`link-${idx}`}
                  x1={sourceNode.position.x}
                  y1={sourceNode.position.y}
                  x2={targetNode.position.x}
                  y2={targetNode.position.y}
                  stroke={linkColor}
                  strokeWidth={linkWidth}
                  opacity={0.6}
                />
              );
            })}
            
            {/* Switches */}
            {switches.map((sw) => (
              <g key={sw.id}>
                <rect
                  x={sw.position.x - 15}
                  y={sw.position.y - 15}
                  width={30}
                  height={30}
                  fill="#fbbf24"
                  stroke="#ffffff"
                  strokeWidth={2}
                  className="cursor-pointer hover:stroke-yellow-400 transition-all"
                  onClick={() => setSelectedNode(sw)}
                />
                <text
                  x={sw.position.x}
                  y={sw.position.y + 35}
                  textAnchor="middle"
                  className="fill-white text-xs font-semibold"
                >
                  {sw.name}
                </text>
              </g>
            ))}
            
            {/* Hosts */}
            {hosts.map((host) => (
              <g key={host.id}>
                <circle
                  cx={host.position.x}
                  cy={host.position.y}
                  r={getHostSize(host)}
                  fill={getHostColor(host)}
                  stroke={selectedNode?.id === host.id ? '#fbbf24' : '#ffffff'}
                  strokeWidth={selectedNode?.id === host.id ? 3 : 2}
                  className="cursor-pointer hover:stroke-yellow-400 transition-all drop-shadow-lg"
                  onClick={() => setSelectedNode(host)}
                />
                {host.alert_count > 0 && (
                  <circle
                    cx={host.position.x + 10}
                    cy={host.position.y - 10}
                    r="5"
                    fill="#ef4444"
                    className="animate-pulse"
                  />
                )}
                <text
                  x={host.position.x}
                  y={host.position.y + getHostSize(host) + 15}
                  textAnchor="middle"
                  className="fill-white text-xs font-semibold"
                >
                  {host.name}
                </text>
                <text
                  x={host.position.x}
                  y={host.position.y + getHostSize(host) + 28}
                  textAnchor="middle"
                  className="fill-gray-300 text-xs"
                >
                  {host.ip}
                </text>
                {host.alert_count > 0 && (
                  <text
                    x={host.position.x}
                    y={host.position.y + getHostSize(host) + 41}
                    textAnchor="middle"
                    className="fill-yellow-300 text-xs font-semibold"
                  >
                    {host.alert_count} alerts
                  </text>
                )}
              </g>
            ))}
          </svg>
        </div>
        
        {/* Legend */}
        <div className="absolute top-4 right-4 bg-gray-800 p-3 rounded-lg text-xs">
          <h4 className="text-white font-semibold mb-2">Legend</h4>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-yellow-500"></div>
              <span className="text-gray-300">Switch</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-300">Server</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-gray-300">Client</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              <span className="text-gray-300">Active Alerts</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const NetworkVisualization = () => {
    const width = 1000;
    const height = 700;
    
    // Intelligent subnet-based positioning
    const centerX = width / 2;
    // const centerY = height / 2; // unused in demo positioning
    
    // Define fixed positions for demo topology
    const demoPositions = {
      'internet': { x: centerX, y: 80, color: '#ef4444', label: 'Internet/Threats' },
      'firewall': { x: centerX, y: 200, color: '#f59e0b', label: 'Firewall' },
      'web_servers': { x: centerX - 150, y: 320, color: '#f59e0b', label: 'Web Servers (DMZ)' },
      'internal_network': { x: centerX + 150, y: 320, color: '#3b82f6', label: 'Internal Network' },
      'database_servers': { x: centerX - 150, y: 480, color: '#10b981', label: 'Database Servers' },
      'management': { x: centerX + 150, y: 480, color: '#8b5cf6', label: 'Management' }
    };
    
    
    const positionedNodes = filteredNodes.map((node) => {
      const pos = demoPositions[node.id];
      return {
        ...node,
        x: pos.x,
        y: pos.y,
        segmentColor: pos.color,
        label: pos.label
      };
    });

    // Define demo connections showing typical attack paths
    const demoConnections = [
      { source: 'internet', target: 'firewall', type: 'attack', severity: 'high' },
      { source: 'firewall', target: 'web_servers', type: 'traffic', severity: 'medium' },
      { source: 'firewall', target: 'internal_network', type: 'traffic', severity: 'low' },
      { source: 'web_servers', target: 'database_servers', type: 'lateral', severity: 'critical' },
      { source: 'internal_network', target: 'database_servers', type: 'access', severity: 'medium' },
      { source: 'internal_network', target: 'management', type: 'escalation', severity: 'high' }
    ];
    
    const relevantEdges = demoConnections.map((conn, index) => {
      const sourceNode = positionedNodes.find(n => n.id === conn.source);
      const targetNode = positionedNodes.find(n => n.id === conn.target);
      return {
        id: `demo-${index}`,
        source: conn.source,
        target: conn.target,
        sourceNode,
        targetNode,
        type: conn.type,
        severity: conn.severity
      };
    }).filter(edge => edge.sourceNode && edge.targetNode);

    return (
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <div className="w-full overflow-x-auto">
          <svg 
            ref={svgRef} 
            width={Math.max(width, 800)} 
            height={Math.max(height, 500)} 
            className="border border-gray-700 min-w-full"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="xMidYMid meet"
          >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Network Zone Backgrounds */}
          {showSubnets && (
            <g>
              {/* Internet Zone */}
              <rect x="350" y="50" width="300" height="80" fill="#ef444420" stroke="#ef4444" strokeWidth="2" rx="10" />
              <text x="365" y="75" className="fill-white text-sm font-bold">INTERNET / THREAT ACTORS</text>
              
              {/* DMZ Zone */}
              <rect x="250" y="170" width="500" height="180" fill="#f59e0b20" stroke="#f59e0b" strokeWidth="2" rx="10" />
              <text x="265" y="195" className="fill-white text-sm font-bold">DMZ (DEMILITARIZED ZONE)</text>
              
              {/* Internal Zones */}
              <rect x="200" y="380" width="600" height="150" fill="#3b82f620" stroke="#3b82f6" strokeWidth="2" rx="10" />
              <text x="215" y="405" className="fill-white text-sm font-bold">INTERNAL CORPORATE NETWORK</text>
            </g>
          )}
          
          {/* Connection Lines */}
          {relevantEdges.map((edge) => {
            const getConnectionColor = (severity) => {
              switch(severity) {
                case 'critical': return '#dc2626';
                case 'high': return '#ea580c';
                case 'medium': return '#d97706';
                default: return '#6b7280';
              }
            };
            
            const getConnectionWidth = (type) => {
              switch(type) {
                case 'attack': return 4;
                case 'lateral': return 3;
                case 'escalation': return 3;
                default: return 2;
              }
            };
            
            return (
              <g key={edge.id}>
                <line
                  x1={edge.sourceNode.x}
                  y1={edge.sourceNode.y}
                  x2={edge.targetNode.x}
                  y2={edge.targetNode.y}
                  stroke={getConnectionColor(edge.severity)}
                  strokeWidth={getConnectionWidth(edge.type)}
                  strokeDasharray={edge.type === 'attack' ? '8,4' : 'none'}
                  opacity={0.8}
                />
                {/* Arrow head */}
                <polygon
                  points={`${edge.targetNode.x-8},${edge.targetNode.y-4} ${edge.targetNode.x},${edge.targetNode.y} ${edge.targetNode.x-8},${edge.targetNode.y+4}`}
                  fill={getConnectionColor(edge.severity)}
                />
              </g>
            );
          })}
          
          {/* Nodes */}
          {positionedNodes.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={getNodeSize(node)}
                fill={node.segmentColor || getNodeColor(node)}
                stroke={selectedNode?.id === node.id ? '#fbbf24' : '#ffffff'}
                strokeWidth={selectedNode?.id === node.id ? 3 : 2}
                className="cursor-pointer hover:stroke-yellow-400 transition-all drop-shadow-lg"
                onClick={() => setSelectedNode(node)}
              />
              {node.alert_count > 0 && (
                <circle
                  cx={node.x + 8}
                  cy={node.y - 8}
                  r="4"
                  fill="#ef4444"
                  className="animate-pulse"
                />
              )}
            </g>
          ))}
          
          {/* Node labels - Always visible for demo */}
          {positionedNodes.map((node) => (
            <g key={`label-${node.id}`}>
              <text
                x={node.x}
                y={node.y + getNodeSize(node) + 20}
                textAnchor="middle"
                className="fill-white text-sm font-bold drop-shadow-lg"
              >
                {node.label}
              </text>
              <text
                x={node.x}
                y={node.y + getNodeSize(node) + 35}
                textAnchor="middle"
                className="fill-yellow-300 text-xs font-semibold"
              >
                {node.alert_count} alerts
              </text>
            </g>
          ))}
          </svg>
        </div>
        
        {/* Responsive Legend */}
        <div className="absolute top-2 right-2 sm:top-4 sm:right-4 bg-gray-800 p-2 sm:p-3 rounded-lg text-xs">
          <h4 className="text-white font-semibold mb-2 hidden sm:block">Legend</h4>
          <div className="space-y-1">
            <div className="flex items-center gap-1 sm:gap-2">
              <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-blue-500"></div>
              <span className="text-gray-300 text-xs">Internal</span>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-300 text-xs">External</span>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <div className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-300 text-xs">Localhost</span>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              <span className="text-gray-300 text-xs">Active Alerts</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-3 sm:space-y-0">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Network Topology</h2>
          <p className="text-sm sm:text-base text-gray-400">Real-time network visualization and threat analysis</p>
        </div>
        <div className="flex gap-2">
          <div className="flex bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('mininet')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'mininet' 
                  ? 'bg-indigo-600 text-white' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Mininet
            </button>
            <button
              onClick={() => setViewMode('alerts')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'alerts' 
                  ? 'bg-indigo-600 text-white' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Alerts
            </button>
          </div>
          <button
            onClick={() => {
              fetchNetworkData();
              fetchMininetTopology();
              fetchConnections();
            }}
            className="flex items-center justify-center px-3 py-2 sm:px-4 sm:py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm sm:text-base"
          >
            <RefreshCw className="h-4 w-4 mr-1 sm:mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Responsive Controls */}
      <div className="bg-gray-800 p-3 sm:p-4 rounded-lg">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-400 text-sm font-medium">Filter:</span>
            <select 
              value={filterType} 
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 text-sm"
            >
              <option value="all">All Segments</option>
              <option value="internal">Internal Only</option>
              <option value="external">External Only</option>
              <option value="high-risk">High Risk</option>
            </select>
          </div>
          
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <span className="text-gray-400 text-sm font-medium">Max Nodes:</span>
            <select 
              value={maxNodes} 
              onChange={(e) => setMaxNodes(parseInt(e.target.value))}
              className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 text-sm"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={showLabels} 
              onChange={(e) => setShowLabels(e.target.checked)}
              className="rounded"
              id="show-labels"
            />
            <label htmlFor="show-labels" className="text-gray-400 text-sm">Show Labels</label>
          </div>
          
          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={showSubnets} 
              onChange={(e) => setShowSubnets(e.target.checked)}
              className="rounded"
              id="show-segments"
            />
            <label htmlFor="show-segments" className="text-gray-400 text-sm">Show Segments</label>
          </div>
        </div>
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center h-64 sm:h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 sm:h-12 sm:w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <div className="text-gray-400 text-sm sm:text-base">Loading network data...</div>
          </div>
        </div>
      ) : (
        viewMode === 'mininet' ? <MininetVisualization /> : <NetworkVisualization />
      )}
      
      {selectedNode && (
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-semibold mb-3 text-base sm:text-lg">
            {selectedNode.name || 'Node'} Details
          </h3>
          <div className="text-sm text-gray-300 space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
              {selectedNode.ip && (
                <p><span className="font-medium">IP Address:</span> {selectedNode.ip}</p>
              )}
              {selectedNode.type && (
                <p><span className="font-medium">Type:</span> {selectedNode.type.toUpperCase()}</p>
              )}
              {selectedNode.segment && (
                <p><span className="font-medium">Segment:</span> {selectedNode.segment.toUpperCase()}</p>
              )}
              {selectedNode.subnet && (
                <p><span className="font-medium">Subnet:</span> {selectedNode.subnet}</p>
              )}
              {selectedNode.alert_count !== undefined && (
                <p><span className="font-medium">Total Alerts:</span> {selectedNode.alert_count}</p>
              )}
              {selectedNode.nodes && (
                <p><span className="font-medium">Hosts:</span> {selectedNode.nodes.length}</p>
              )}
            </div>
            
            {selectedNode.services && selectedNode.services.length > 0 && (
              <p><span className="font-medium">Services:</span> {selectedNode.services.join(', ')}</p>
            )}
            
            {selectedNode.ports && selectedNode.ports.length > 0 && (
              <p><span className="font-medium">Ports:</span> {selectedNode.ports.join(', ')}</p>
            )}
            
            {selectedNode.representative_ip && (
              <p><span className="font-medium">Representative IP:</span> {selectedNode.representative_ip}</p>
            )}
            
            {selectedNode.severity_counts && (
              <div>
                <span className="font-medium">Severity Distribution:</span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 ml-4 mt-2">
                  {Object.entries(selectedNode.severity_counts).map(([severity, count]) => (
                    count > 0 && (
                      <div key={severity} className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full flex-shrink-0" 
                          style={{ backgroundColor: getSeverityColor(severity) }}
                        ></div>
                        <span className="text-xs">{severity}: {count}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}
            
            {selectedNode.attack_types && selectedNode.attack_types.length > 0 && (
              <div>
                <span className="font-medium">Attack Types:</span>
                <div className="ml-4 mt-1 flex flex-wrap gap-1">
                  {selectedNode.attack_types.map((type, idx) => (
                    <span key={idx} className="px-2 py-1 bg-red-900 text-red-200 rounded text-xs">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {selectedNode.nodes && selectedNode.nodes.length > 1 && (
              <div className="mt-3">
                <span className="font-medium">Sample IPs:</span>
                <div className="ml-4 text-xs font-mono mt-1 max-h-20 overflow-y-auto">
                  {selectedNode.nodes.slice(0, 5).map(node => (
                    <div key={node.id} className="py-0.5">{node.id}</div>
                  ))}
                  {selectedNode.nodes.length > 5 && (
                    <div className="text-gray-400 py-0.5">... and {selectedNode.nodes.length - 5} more</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkMap;
