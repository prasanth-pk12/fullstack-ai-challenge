import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  PlusIcon, 
  FunnelIcon, 
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { tasksAPI } from '../services/api';
import { useTaskEvents } from '../hooks/useWebSocket';
import Navigation from '../components/Navigation';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import AttachmentViewer from '../components/AttachmentViewer';
import ConnectionStatus from '../components/ConnectionStatus';
import Quote from '../components/Quote';
import toast from 'react-hot-toast';

const Tasks = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [filteredTasks, setFilteredTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFormLoading, setIsFormLoading] = useState(false);
  const [deletingTaskIds, setDeletingTaskIds] = useState(new Set());
  const [updatingStatusIds, setUpdatingStatusIds] = useState(new Set());
  
  // Modal states
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [showAttachments, setShowAttachments] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  
  // Filter and search states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // WebSocket real-time task updates
  const [recentlyUpdatedTasks, setRecentlyUpdatedTasks] = useState(new Set());

  const handleTaskCreated = useCallback((task, eventUser) => {
    setTasks(prevTasks => {
      // Avoid duplicates - check if task already exists
      if (prevTasks.find(t => t.id === task.id)) {
        return prevTasks;
      }
      
      const newTasks = [task, ...prevTasks];
      console.log('Task created via WebSocket:', task, 'by user:', eventUser);
      
      // Show toast notification if task was created by another user
      if (user && eventUser && eventUser.id !== user.id) {
        toast.success(`New task "${task.title}" was created by ${eventUser.username || eventUser.name}`);
      }
      
      // Mark as recently updated for animation
      setRecentlyUpdatedTasks(prev => new Set([...prev, task.id]));
      setTimeout(() => {
        setRecentlyUpdatedTasks(prev => {
          const newSet = new Set(prev);
          newSet.delete(task.id);
          return newSet;
        });
      }, 1000);
      
      return newTasks;
    });
  }, [user]);

  const handleTaskUpdated = useCallback((task, eventUser) => {
    setTasks(prevTasks => {
      const newTasks = prevTasks.map(t => 
        t.id === task.id ? { ...t, ...task } : t
      );
      
      console.log('Task updated via WebSocket:', task, 'by user:', eventUser);
      
      // Show toast notification if task was updated by another user
      if (user && eventUser && eventUser.id !== user.id) {
        toast(`Task "${task.title}" was updated by ${eventUser.username || eventUser.name}`, {
          icon: 'ℹ️',
        });
      }
      
      // Mark as recently updated for animation
      setRecentlyUpdatedTasks(prev => new Set([...prev, task.id]));
      setTimeout(() => {
        setRecentlyUpdatedTasks(prev => {
          const newSet = new Set(prev);
          newSet.delete(task.id);
          return newSet;
        });
      }, 1000);
      
      return newTasks;
    });
  }, [user]);

  const handleTaskDeleted = useCallback((taskId, eventUser) => {
    setTasks(prevTasks => {
      const taskToDelete = prevTasks.find(t => t.id === taskId);
      const newTasks = prevTasks.filter(t => t.id !== taskId);
      
      console.log('Task deleted via WebSocket:', taskId, 'by user:', eventUser);
      
      // Show toast notification if task was deleted by another user
      if (user && eventUser && eventUser.id !== user.id && taskToDelete) {
        toast(`Task "${taskToDelete.title}" was deleted by ${eventUser.username || eventUser.name}`, {
          icon: '⚠️',
          style: {
            borderLeft: '4px solid #f59e0b',
          }
        });
      }
      
      return newTasks;
    });
  }, [user]);

  // Set up WebSocket event handlers
  useTaskEvents({
    onTaskCreated: handleTaskCreated,
    onTaskUpdated: handleTaskUpdated,
    onTaskDeleted: handleTaskDeleted
  });

  useEffect(() => {
    loadTasks();
    loadStats();
  }, []);

  useEffect(() => {
    const applyFilters = () => {
      let filtered = [...tasks];

      // Search filter
      if (searchTerm) {
        filtered = filtered.filter(task =>
          task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (task.description && task.description.toLowerCase().includes(searchTerm.toLowerCase()))
        );
      }

      // Status filter
      if (statusFilter !== 'ALL') {
        filtered = filtered.filter(task => task.status === statusFilter);
      }

      // Sort
      filtered.sort((a, b) => {
        let aValue = a[sortBy];
        let bValue = b[sortBy];

        if (sortBy === 'due_date') {
          aValue = aValue ? new Date(aValue) : new Date('9999-12-31');
          bValue = bValue ? new Date(bValue) : new Date('9999-12-31');
        } else if (sortBy === 'created_at' || sortBy === 'updated_at') {
          aValue = new Date(aValue);
          bValue = new Date(bValue);
        } else if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        if (sortOrder === 'asc') {
          return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
          return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
      });

      setFilteredTasks(filtered);
    };

    applyFilters();
  }, [tasks, searchTerm, statusFilter, sortBy, sortOrder]);

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const data = await tasksAPI.getTasks(0, 1000); // Load all tasks
      setTasks(data);
    } catch (error) {
      toast.error('Failed to load tasks');
      console.error('Error loading tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      await tasksAPI.getTaskStats();
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleCreateTask = async (taskData, newAttachmentFile = null) => {
    setIsFormLoading(true);
    try {
      const newTask = await tasksAPI.createTask(taskData);
      
      // Upload attachment if provided
      if (newAttachmentFile) {
        try {
          await tasksAPI.uploadFile(newTask.id, newAttachmentFile);
          toast.success('Task created with attachment!');
        } catch (uploadError) {
          toast('Task created but attachment failed to upload', {
            icon: '⚠️',
            style: {
              borderLeft: '4px solid #f59e0b',
            }
          });
          console.error('Attachment upload error:', uploadError);
        }
      } else {
        toast.success('Task created successfully!');
      }
      
      // Always add to local state immediately for instant UI feedback
      // WebSocket will sync any updates/conflicts from other users
      setTasks(prevTasks => {
        // Avoid duplicates - check if task already exists
        if (prevTasks.find(t => t.id === newTask.id)) {
          return prevTasks;
        }
        return [newTask, ...prevTasks];
      });
      
      await loadStats();
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create task');
    } finally {
      setIsFormLoading(false);
    }
  };

  const handleEditTask = async (taskData, newAttachmentFile = null, removeExistingAttachment = false) => {
    setIsFormLoading(true);
    try {
      // Remove existing attachment if requested
      if (removeExistingAttachment && editingTask.attachment) {
        await tasksAPI.deleteAttachment(editingTask.attachment.id);
      }

      // Update the task data
      const updatedTask = await tasksAPI.updateTask(editingTask.id, taskData);
      
      // Upload new attachment if provided
      if (newAttachmentFile) {
        await tasksAPI.uploadFile(editingTask.id, newAttachmentFile);
      }

      // Always update local state immediately for instant UI feedback
      // WebSocket will sync any updates/conflicts from other users
      setTasks(prevTasks => prevTasks.map(task =>
        task.id === editingTask.id ? { ...task, ...updatedTask } : task
      ));
      
      toast.success('Task updated successfully!');
      setEditingTask(null);
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update task');
    } finally {
      setIsFormLoading(false);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    setDeletingTaskIds(prev => new Set([...prev, taskId]));
    try {
      await tasksAPI.deleteTask(taskId);
      // Always update local state immediately for instant UI feedback
      // WebSocket will sync any updates/conflicts from other users
      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      toast.success('Task deleted successfully');
      await loadStats();
    } catch (error) {
      toast.error('Failed to delete task');
      console.error('Error deleting task:', error);
    } finally {
      setDeletingTaskIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    setUpdatingStatusIds(prev => new Set([...prev, taskId]));
    try {
      const updatedTask = await tasksAPI.updateTask(taskId, { status: newStatus });
      // Always update local state immediately for instant UI feedback
      // WebSocket will sync any updates/conflicts from other users
      setTasks(prevTasks => prevTasks.map(task =>
        task.id === taskId ? { ...task, ...updatedTask } : task
      ));
      toast.success('Task status updated');
    } catch (error) {
      toast.error('Failed to update task status');
      console.error('Error updating status:', error);
    } finally {
      setUpdatingStatusIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
    }
  };

  const handleOpenAttachments = (task) => {
    setSelectedTask(task);
    setShowAttachments(true);
  };

  const getTaskCountByStatus = (status) => {
    return tasks.filter(task => task.status === status).length;
  };

  const getOverdueTasks = () => {
    return tasks.filter(task => 
      task.due_date && 
      new Date(task.due_date) < new Date() && 
      task.status !== 'done'
    ).length;
  };

  const statusOptions = [
    { value: 'ALL', label: 'All Tasks', count: tasks.length },
    { value: 'todo', label: 'To Do', count: getTaskCountByStatus('todo') },
    { value: 'in-progress', label: 'In Progress', count: getTaskCountByStatus('in-progress') },
    { value: 'done', label: 'Done', count: getTaskCountByStatus('done') }
  ];

  const sortOptions = [
    { value: 'created_at', label: 'Created Date' },
    { value: 'updated_at', label: 'Updated Date' },
    { value: 'due_date', label: 'Due Date' },
    { value: 'title', label: 'Title' },
    { value: 'status', label: 'Status' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />
      
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
              <p className="text-sm text-gray-600">
                Manage your tasks efficiently
              </p>
            </div>
            <button
              onClick={() => setShowTaskForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              New Task
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards and Inspiration */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Connection Status */}
        <ConnectionStatus className="mb-6" />
        
        {/* Quote Component */}
        <Quote className="mb-6" autoRefresh={true} refreshInterval={60000} />
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <CheckCircleIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Tasks</p>
                <p className="text-2xl font-bold text-gray-900">{tasks.length}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <ClockIcon className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">In Progress</p>
                <p className="text-2xl font-bold text-gray-900">{getTaskCountByStatus('in-progress')}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircleIcon className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-bold text-gray-900">{getTaskCountByStatus('done')}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Overdue</p>
                <p className="text-2xl font-bold text-gray-900">{getOverdueTasks()}</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search tasks..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label} ({option.count})
                  </option>
                ))}
              </select>
              <FunnelIcon className="absolute right-2 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>

            {/* Sort By */}
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
              >
                <ChevronDownIcon 
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    sortOrder === 'asc' ? 'rotate-180' : ''
                  }`} 
                />
              </button>
            </div>
          </div>

          {/* Active Filters */}
          {(searchTerm || statusFilter !== 'ALL') && (
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-200">
              <span className="text-sm text-gray-500">Active filters:</span>
              {searchTerm && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">
                  Search: "{searchTerm}"
                  <button onClick={() => setSearchTerm('')} className="text-blue-600 hover:text-blue-800">
                    ×
                  </button>
                </span>
              )}
              {statusFilter !== 'ALL' && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-xs">
                  Status: {statusOptions.find(o => o.value === statusFilter)?.label}
                  <button onClick={() => setStatusFilter('ALL')} className="text-purple-600 hover:text-purple-800">
                    ×
                  </button>
                </span>
              )}
            </div>
          )}
        </div>

        {/* Tasks Grid */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircleIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
              <p className="text-gray-500 mb-4">
                {tasks.length === 0 
                  ? "Get started by creating your first task!" 
                  : "Try adjusting your search or filters."}
              </p>
              {tasks.length === 0 && (
                <button
                  onClick={() => setShowTaskForm(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PlusIcon className="w-5 h-5" />
                  Create Your First Task
                </button>
              )}
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {filteredTasks.map((task) => (
                <TaskCard
                  key={`task-${task.id}`}
                  task={task}
                  onEdit={setEditingTask}
                  onDelete={handleDeleteTask}
                  onStatusChange={handleStatusChange}
                  onViewAttachments={handleOpenAttachments}
                  animateUpdate={recentlyUpdatedTasks.has(task.id)}
                  isDeleting={deletingTaskIds.has(task.id)}
                  isUpdatingStatus={updatingStatusIds.has(task.id)}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Task Form Modal */}
      <TaskForm
        isOpen={showTaskForm || !!editingTask}
        onClose={() => {
          setShowTaskForm(false);
          setEditingTask(null);
        }}
        onSubmit={editingTask ? handleEditTask : handleCreateTask}
        task={editingTask}
        isLoading={isFormLoading}
      />

      {/* Attachments Modal */}
      <AttachmentViewer
        isOpen={showAttachments}
        onClose={() => {
          setShowAttachments(false);
          setSelectedTask(null);
        }}
        task={selectedTask}
        onAttachmentAdded={() => loadTasks()}
        onAttachmentDeleted={() => loadTasks()}
      />
    </div>
  );
};

export default Tasks;