// Modern Admin Dashboard - Rebuilt from scratch with comprehensive features
const { useState, useEffect } = React;
const { 
  Users, UserPlus, Edit3, Trash2, Shield, Eye, EyeOff, Save, X, 
  Search, Filter, CheckSquare, Square, AlertCircle, UserCheck, UserX, Activity
} = lucide;

const AdminDashboard = ({ token, userRole, onLogout }) => {
  // State Management
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // UI State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Form State
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'viewer',
    active: true
  });
  
  const [editingUser, setEditingUser] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  
  // Statistics
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    superAdmins: 0,
    analysts: 0,
    viewers: 0
  });

  const API_BASE = window.location.origin;

  // Initialize
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchUsers(), fetchRoles()]);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch users');
      
      const data = await response.json();
      const userList = data.users || [];
      setUsers(userList);
      calculateStats(userList);
    } catch (err) {
      throw new Error('Failed to fetch users');
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/roles`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRoles(data.roles || []);
      } else {
        setRoles([
          { name: 'Super Admin', value: 'super_admin' },
          { name: 'Analyst', value: 'analyst' },
          { name: 'Viewer', value: 'viewer' }
        ]);
      }
    } catch (err) {
      setRoles([
        { name: 'Super Admin', value: 'super_admin' },
        { name: 'Analyst', value: 'analyst' },
        { name: 'Viewer', value: 'viewer' }
      ]);
    }
  };

  const calculateStats = (userList) => {
    const active = userList.filter(u => u.active).length;
    const superAdmins = userList.filter(u => u.role === 'super_admin').length;
    const analysts = userList.filter(u => u.role === 'analyst').length;
    const viewers = userList.filter(u => u.role === 'viewer').length;
    
    setStats({
      totalUsers: userList.length,
      activeUsers: active,
      superAdmins,
      analysts,
      viewers
    });
  };

  // CRUD Operations
  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!newUser.username.trim()) {
      setError('Username is required');
      return;
    }
    
    if (!newUser.password || newUser.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUser)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to create user');
      }

      setSuccess(`User "${newUser.username}" created successfully`);
      setNewUser({ username: '', password: '', role: 'viewer', active: true });
      setShowCreateModal(false);
      await fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    setError('');
    setSuccess('');

    try {
      const updateData = {
        role: editingUser.role,
        active: editingUser.active
      };
      
      if (editingUser.password) {
        updateData.password = editingUser.password;
      }

      const response = await fetch(`${API_BASE}/api/admin/users/${editingUser.username}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to update user');
      }

      setSuccess(`User "${editingUser.username}" updated successfully`);
      setShowEditModal(false);
      setEditingUser(null);
      await fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE}/api/admin/users/${username}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to delete user');
      }

      setSuccess(`User "${username}" deleted successfully`);
      await fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedUsers.length === 0) {
      setError('No users selected');
      return;
    }

    const actionText = action === 'activate' ? 'activate' : 
                      action === 'deactivate' ? 'deactivate' : 'delete';
    
    if (!window.confirm(`Are you sure you want to ${actionText} ${selectedUsers.length} user(s)?`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const promises = selectedUsers.map(username => {
        if (action === 'delete') {
          return fetch(`${API_BASE}/api/admin/users/${username}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
          });
        } else {
          return fetch(`${API_BASE}/api/admin/users/${username}`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ active: action === 'activate' })
          });
        }
      });

      await Promise.all(promises);
      setSuccess(`Successfully ${actionText}d ${selectedUsers.length} user(s)`);
      setSelectedUsers([]);
      await fetchUsers();
    } catch (err) {
      setError(`Failed to ${actionText} users`);
    }
  };

  // Utility functions
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && user.active) ||
                         (statusFilter === 'inactive' && !user.active);
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleColor = (role) => {
    const colors = {
      'super_admin': 'bg-red-100 text-red-800 border-red-200',
      'analyst': 'bg-blue-100 text-blue-800 border-blue-200',
      'viewer': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[role] || colors['viewer'];
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'super_admin': return Shield;
      case 'analyst': return Activity;
      case 'viewer': return Eye;
      default: return Users;
    }
  };

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  // Loading state
  if (loading) {
    return React.createElement('div', { className: 'flex justify-center items-center h-96' },
      React.createElement('div', { className: 'text-center' },
        React.createElement('div', { className: 'animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4' }),
        React.createElement('p', { className: 'text-gray-600' }, 'Loading admin dashboard...')
      )
    );
  }

  return React.createElement('div', { className: 'max-w-7xl mx-auto p-6 space-y-6' },
    // Header with Statistics
    React.createElement('div', { className: 'bg-white rounded-lg shadow-sm border border-gray-200 p-6' },
      React.createElement('div', { className: 'flex items-center justify-between mb-6' },
        React.createElement('div', null,
          React.createElement('h1', { className: 'text-3xl font-bold text-gray-900 flex items-center' },
            React.createElement(Shield, { className: 'mr-3 text-blue-600', size: 32 }),
            'Admin Dashboard'
          ),
          React.createElement('p', { className: 'text-gray-600 mt-2' }, 
            'Manage users, roles, and system settings'
          )
        ),
        React.createElement('button', {
          onClick: () => setShowCreateModal(true),
          className: 'bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors'
        },
          React.createElement(UserPlus, { size: 20, className: 'mr-2' }),
          'Add User'
        )
      ),

      // Statistics Cards
      React.createElement('div', { className: 'grid grid-cols-1 md:grid-cols-5 gap-4' },
        React.createElement('div', { className: 'bg-blue-50 p-4 rounded-lg border border-blue-200' },
          React.createElement('div', { className: 'flex items-center justify-between' },
            React.createElement('div', null,
              React.createElement('p', { className: 'text-sm font-medium text-blue-600' }, 'Total Users'),
              React.createElement('p', { className: 'text-2xl font-bold text-blue-900' }, stats.totalUsers)
            ),
            React.createElement(Users, { className: 'text-blue-600', size: 24 })
          )
        ),
        React.createElement('div', { className: 'bg-green-50 p-4 rounded-lg border border-green-200' },
          React.createElement('div', { className: 'flex items-center justify-between' },
            React.createElement('div', null,
              React.createElement('p', { className: 'text-sm font-medium text-green-600' }, 'Active'),
              React.createElement('p', { className: 'text-2xl font-bold text-green-900' }, stats.activeUsers)
            ),
            React.createElement(UserCheck, { className: 'text-green-600', size: 24 })
          )
        ),
        React.createElement('div', { className: 'bg-red-50 p-4 rounded-lg border border-red-200' },
          React.createElement('div', { className: 'flex items-center justify-between' },
            React.createElement('div', null,
              React.createElement('p', { className: 'text-sm font-medium text-red-600' }, 'Super Admins'),
              React.createElement('p', { className: 'text-2xl font-bold text-red-900' }, stats.superAdmins)
            ),
            React.createElement(Shield, { className: 'text-red-600', size: 24 })
          )
        ),
        React.createElement('div', { className: 'bg-purple-50 p-4 rounded-lg border border-purple-200' },
          React.createElement('div', { className: 'flex items-center justify-between' },
            React.createElement('div', null,
              React.createElement('p', { className: 'text-sm font-medium text-purple-600' }, 'Analysts'),
              React.createElement('p', { className: 'text-2xl font-bold text-purple-900' }, stats.analysts)
            ),
            React.createElement(Activity, { className: 'text-purple-600', size: 24 })
          )
        ),
        React.createElement('div', { className: 'bg-gray-50 p-4 rounded-lg border border-gray-200' },
          React.createElement('div', { className: 'flex items-center justify-between' },
            React.createElement('div', null,
              React.createElement('p', { className: 'text-sm font-medium text-gray-600' }, 'Viewers'),
              React.createElement('p', { className: 'text-2xl font-bold text-gray-900' }, stats.viewers)
            ),
            React.createElement(Eye, { className: 'text-gray-600', size: 24 })
          )
        )
      )
    ),

    // Messages
    error && React.createElement('div', { 
      className: 'bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between' 
    },
      React.createElement('div', { className: 'flex items-center' },
        React.createElement(AlertCircle, { size: 20, className: 'mr-2' }),
        error
      ),
      React.createElement('button', { onClick: clearMessages, className: 'text-red-500 hover:text-red-700' },
        React.createElement(X, { size: 16 })
      )
    ),

    success && React.createElement('div', { 
      className: 'bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center justify-between' 
    },
      React.createElement('div', { className: 'flex items-center' },
        React.createElement(UserCheck, { size: 20, className: 'mr-2' }),
        success
      ),
      React.createElement('button', { onClick: clearMessages, className: 'text-green-500 hover:text-green-700' },
        React.createElement(X, { size: 16 })
      )
    ),

    // Main Content Area
    React.createElement('div', { className: 'bg-white rounded-lg shadow-sm border border-gray-200' },
      // Filters and Search
      React.createElement('div', { className: 'p-6 border-b border-gray-200' },
        React.createElement('div', { className: 'flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0' },
          React.createElement('div', { className: 'flex items-center space-x-4' },
            React.createElement('div', { className: 'relative' },
              React.createElement('input', {
                type: 'text',
                placeholder: 'Search users...',
                value: searchTerm,
                onChange: (e) => setSearchTerm(e.target.value),
                className: 'pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-64'
              }),
              React.createElement(Search, { 
                className: 'absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400', 
                size: 16 
              })
            ),
            React.createElement('select', {
              value: roleFilter,
              onChange: (e) => setRoleFilter(e.target.value),
              className: 'px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            },
              React.createElement('option', { value: 'all' }, 'All Roles'),
              roles.map(role => 
                React.createElement('option', { key: role.value, value: role.value }, role.name)
              )
            ),
            React.createElement('select', {
              value: statusFilter,
              onChange: (e) => setStatusFilter(e.target.value),
              className: 'px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            },
              React.createElement('option', { value: 'all' }, 'All Status'),
              React.createElement('option', { value: 'active' }, 'Active'),
              React.createElement('option', { value: 'inactive' }, 'Inactive')
            )
          ),
          
          // Bulk Actions
          selectedUsers.length > 0 && React.createElement('div', { className: 'flex items-center space-x-2' },
            React.createElement('span', { className: 'text-sm text-gray-600' }, 
              `${selectedUsers.length} selected`
            ),
            React.createElement('button', {
              onClick: () => handleBulkAction('activate'),
              className: 'px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 transition-colors'
            }, 'Activate'),
            React.createElement('button', {
              onClick: () => handleBulkAction('deactivate'),
              className: 'px-3 py-1 bg-yellow-100 text-yellow-700 rounded text-sm hover:bg-yellow-200 transition-colors'
            }, 'Deactivate'),
            React.createElement('button', {
              onClick: () => handleBulkAction('delete'),
              className: 'px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200 transition-colors'
            }, 'Delete')
          )
        )
      ),

      // Users Table
      React.createElement('div', { className: 'overflow-x-auto' },
        React.createElement('table', { className: 'w-full' },
          React.createElement('thead', { className: 'bg-gray-50' },
            React.createElement('tr', null,
              React.createElement('th', { className: 'px-6 py-3 text-left' },
                React.createElement('input', {
                  type: 'checkbox',
                  checked: selectedUsers.length === filteredUsers.length && filteredUsers.length > 0,
                  onChange: (e) => {
                    if (e.target.checked) {
                      setSelectedUsers(filteredUsers.map(u => u.username));
                    } else {
                      setSelectedUsers([]);
                    }
                  },
                  className: 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                })
              ),
              React.createElement('th', { className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider' }, 'User'),
              React.createElement('th', { className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider' }, 'Role'),
              React.createElement('th', { className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider' }, 'Status'),
              React.createElement('th', { className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider' }, 'Created'),
              React.createElement('th', { className: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider' }, 'Actions')
            )
          ),
          React.createElement('tbody', { className: 'bg-white divide-y divide-gray-200' },
            filteredUsers.length === 0 ? 
              React.createElement('tr', null,
                React.createElement('td', { colSpan: 6, className: 'px-6 py-12 text-center' },
                  React.createElement('div', { className: 'text-gray-500' },
                    React.createElement(Users, { size: 48, className: 'mx-auto mb-4 text-gray-300' }),
                    React.createElement('p', null, 'No users found'),
                    React.createElement('p', { className: 'text-sm' }, 'Try adjusting your search or filters')
                  )
                )
              ) :
              filteredUsers.map((user) => {
                const RoleIcon = getRoleIcon(user.role);
                return React.createElement('tr', { 
                  key: user.username, 
                  className: 'hover:bg-gray-50 transition-colors' 
                },
                  React.createElement('td', { className: 'px-6 py-4' },
                    React.createElement('input', {
                      type: 'checkbox',
                      checked: selectedUsers.includes(user.username),
                      onChange: (e) => {
                        if (e.target.checked) {
                          setSelectedUsers([...selectedUsers, user.username]);
                        } else {
                          setSelectedUsers(selectedUsers.filter(u => u !== user.username));
                        }
                      },
                      className: 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                    })
                  ),
                  React.createElement('td', { className: 'px-6 py-4 whitespace-nowrap' },
                    React.createElement('div', { className: 'flex items-center' },
                      React.createElement('div', { className: 'flex-shrink-0 h-10 w-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center' },
                        React.createElement('span', { className: 'text-sm font-semibold text-white' },
                          user.username.charAt(0).toUpperCase()
                        )
                      ),
                      React.createElement('div', { className: 'ml-4' },
                        React.createElement('div', { className: 'text-sm font-medium text-gray-900' }, user.username),
                        React.createElement('div', { className: 'text-sm text-gray-500' }, 
                          user.last_login ? `Last login: ${new Date(user.last_login).toLocaleDateString()}` : 'Never logged in'
                        )
                      )
                    )
                  ),
                  React.createElement('td', { className: 'px-6 py-4 whitespace-nowrap' },
                    React.createElement('div', { className: 'flex items-center' },
                      React.createElement(RoleIcon, { size: 16, className: 'mr-2 text-gray-500' }),
                      React.createElement('span', { 
                        className: `inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getRoleColor(user.role)}` 
                      },
                        user.role.replace('_', ' ').toUpperCase()
                      )
                    )
                  ),
                  React.createElement('td', { className: 'px-6 py-4 whitespace-nowrap' },
                    React.createElement('span', { 
                      className: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }` 
                    },
                      user.active ? 
                        React.createElement(React.Fragment, null,
                          React.createElement('div', { className: 'w-1.5 h-1.5 bg-green-400 rounded-full mr-1' }),
                          'Active'
                        ) :
                        React.createElement(React.Fragment, null,
                          React.createElement('div', { className: 'w-1.5 h-1.5 bg-red-400 rounded-full mr-1' }),
                          'Inactive'
                        )
                    )
                  ),
                  React.createElement('td', { className: 'px-6 py-4 whitespace-nowrap text-sm text-gray-500' },
                    user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'
                  ),
                  React.createElement('td', { className: 'px-6 py-4 whitespace-nowrap text-sm font-medium' },
                    React.createElement('div', { className: 'flex items-center space-x-2' },
                      React.createElement('button', {
                        onClick: () => {
                          setEditingUser({ ...user, password: '' });
                          setShowEditModal(true);
                        },
                        className: 'text-blue-600 hover:text-blue-900 p-1 rounded hover:bg-blue-50 transition-colors'
                      }, React.createElement(Edit3, { size: 16 })),
                      React.createElement('button', {
                        onClick: () => handleDeleteUser(user.username),
                        className: 'text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors'
                      }, React.createElement(Trash2, { size: 16 }))
                    )
                  )
                );
              })
          )
        )
      ),

      // Table Footer
      React.createElement('div', { className: 'px-6 py-3 bg-gray-50 border-t border-gray-200' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('div', { className: 'text-sm text-gray-700' },
            `Showing ${filteredUsers.length} of ${users.length} users`
          ),
          React.createElement('div', { className: 'text-sm text-gray-500' },
            `${selectedUsers.length} selected`
          )
        )
      )
    ),

    // Create User Modal
    showCreateModal && React.createElement('div', { className: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4' },
      React.createElement('div', { className: 'bg-white rounded-lg shadow-xl w-full max-w-md' },
        React.createElement('div', { className: 'flex items-center justify-between p-6 border-b border-gray-200' },
          React.createElement('h2', { className: 'text-xl font-semibold text-gray-900' }, 'Create New User'),
          React.createElement('button', {
            onClick: () => {
              setShowCreateModal(false);
              setNewUser({ username: '', password: '', role: 'viewer', active: true });
              clearMessages();
            },
            className: 'text-gray-400 hover:text-gray-600 transition-colors'
          }, React.createElement(X, { size: 24 }))
        ),

        React.createElement('form', { onSubmit: handleCreateUser, className: 'p-6 space-y-4' },
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-sm font-medium text-gray-700 mb-2' }, 'Username'),
            React.createElement('input', {
              type: 'text',
              value: newUser.username,
              onChange: (e) => setNewUser({...newUser, username: e.target.value}),
              className: 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              placeholder: 'Enter username',
              required: true
            })
          ),

          React.createElement('div', null,
            React.createElement('label', { className: 'block text-sm font-medium text-gray-700 mb-2' }, 'Password'),
            React.createElement('div', { className: 'relative' },
              React.createElement('input', {
                type: showPassword ? "text" : "password",
                value: newUser.password,
                onChange: (e) => setNewUser({...newUser, password: e.target.value}),
                className: 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10',
                placeholder: 'Enter password (min 8 characters)',
                required: true,
                minLength: 8
              }),
              React.createElement('button', {
                type: 'button',
                onClick: () => setShowPassword(!showPassword),
                className: 'absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600'
              }, showPassword ? React.createElement(EyeOff, { size: 16 }) : React.createElement(Eye, { size: 16 }))
            )
          ),

          React.createElement('div', null,
            React.createElement('label', { className: 'block text-sm font-medium text-gray-700 mb-2' }, 'Role'),
            React.createElement('select', {
              value: newUser.role,
              onChange: (e) => setNewUser({...newUser, role: e.target.value}),
              className: 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            },
              roles.map(role => 
                React.createElement('option', { key: role.value, value: role.value }, role.name)
              )
            )
          ),

          React.createElement('div', { className: 'flex items-center' },
            React.createElement('input', {
              type: 'checkbox',
              id: 'active',
              checked: newUser.active,
              onChange: (e) => setNewUser({...newUser, active: e.target.checked}),
              className: 'rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2'
            }),
            React.createElement('label', { htmlFor: 'active', className: 'text-sm text-gray-700' }, 'Active user')
          ),

          React.createElement('div', { className: 'flex space-x-3 pt-4' },
            React.createElement('button', {
              type: 'submit',
              className: 'flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors'
            }, 'Create User'),
            React.createElement('button', {
              type: 'button',
              onClick: () => {
                setShowCreateModal(false);
                setNewUser({ username: '', password: '', role: 'viewer', active: true });
              },
              className: 'flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded-lg transition-colors'
            }, 'Cancel')
          )
        )
      )
    ),

    // Edit User Modal
    showEditModal && editingUser && React.createElement('div', { className: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4' },
      React.createElement('div', { className: 'bg-white rounded-lg shadow-xl w-full max-w-md' },
        React.createElement('div', { className: 'flex items-center justify-between p-6 border-b border-gray-200' },
          React.createElement('h2', { className: 'text-xl font-semibold text-gray-900' }, `Edit User: ${editingUser.username}`),
          React.createElement('button', {
            onClick: () => {
              setShowEditModal(false);
              setEditingUser(null);
              clearMessages();
            },
            className: 'text-gray-400 hover:text-gray-600 transition-colors'
          }, React.createElement(X, { size: 24 }))
        ),

        React.createElement('div', { className: 'p-6 space-y-4' },
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-sm font-medium text-gray-700 mb-2' }, 'Role'),
            React.createElement('select', {
              value: editingUser.role,
              onChange: (e) => setEditingUser({...editingUser, role: e.target.value}),
              className: 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            },
              roles.map(role => 
                React.createElement('option', { key: role.value, value: role.value }, role.name)
              )
            )
          ),

          React.createElement('div', { className: 'flex items-center' },
            React.createElement('input', {
              type: 'checkbox',
              id: 'editActive',
              checked: editingUser.active,
              onChange: (e) => setEditingUser({...editingUser, active: e.target.checked}),
              className: 'rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2'
            }),
            React.createElement('label', { htmlFor: 'editActive', className: 'text-sm text-gray-700' }, 'Active user')
          ),

          React.createElement('div', null,
            React.createElement('label', { className: 'block text-sm font-medium text-gray-700 mb-2' }, 'New Password (optional)'),
            React.createElement('input', {
              type: 'password',
              value: editingUser.password || '',
              onChange: (e) => setEditingUser({...editingUser, password: e.target.value}),
              className: 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
              placeholder: 'Leave blank to keep current password'
            })
          ),

          React.createElement('div', { className: 'flex space-x-3 pt-4' },
            React.createElement('button', {
              onClick: handleUpdateUser,
              className: 'flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center'
            },
              React.createElement(Save, { size: 16, className: 'mr-2' }),
              'Save Changes'
            ),
            React.createElement('button', {
              onClick: () => {
                setShowEditModal(false);
                setEditingUser(null);
              },
              className: 'flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded-lg transition-colors'
            }, 'Cancel')
          )
        )
      )
    )
  );
};

// Export to global scope
window.AdminDashboard = AdminDashboard;
