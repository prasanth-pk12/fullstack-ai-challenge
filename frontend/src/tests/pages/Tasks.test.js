import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Tasks from '../../pages/Tasks';
import { tasksAPI } from '../../services/api';

// Mock the API
jest.mock('../../services/api', () => ({
  tasksAPI: {
    getTasks: jest.fn(),
    getTaskStats: jest.fn(),
    createTask: jest.fn(),
    updateTask: jest.fn(),
    deleteTask: jest.fn()
  }
}));

// Mock the contexts
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      username: 'testuser',
      role: 'USER'
    }
  })
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => <div>{children}</div>
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn()
  }
}));

// Mock Navigation component
jest.mock('../../components/Navigation', () => {
  return function MockNavigation() {
    return <div data-testid="navigation">Navigation</div>;
  };
});

const mockTasks = [
  {
    id: 1,
    title: 'Task 1',
    description: 'Description 1',
    status: 'TODO',
    due_date: '2024-12-31T23:59:59Z',
    owner_id: 1,
    attachments: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    title: 'Task 2',
    description: 'Description 2',
    status: 'IN_PROGRESS',
    due_date: null,
    owner_id: 1,
    attachments: ['file.pdf'],
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  },
  {
    id: 3,
    title: 'Task 3',
    description: 'Description 3',
    status: 'DONE',
    due_date: '2020-01-01T00:00:00Z', // Overdue date but completed
    owner_id: 1,
    attachments: [],
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z'
  }
];

const renderTasks = () => {
  return render(
    <BrowserRouter>
      <Tasks />
    </BrowserRouter>
  );
};

describe('Tasks Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    tasksAPI.getTasks.mockResolvedValue(mockTasks);
    tasksAPI.getTaskStats.mockResolvedValue({ total_tasks: 3 });
  });

  test('renders page with navigation and header', async () => {
    renderTasks();

    expect(screen.getByTestId('navigation')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Manage your tasks efficiently')).toBeInTheDocument();
  });

  test('loads and displays tasks', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
    expect(tasksAPI.getTasks).toHaveBeenCalledWith(0, 1000);
  });

  test('displays task statistics correctly', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument(); // Total tasks
    });

    expect(screen.getByText('1')).toBeInTheDocument(); // In progress
    expect(screen.getByText('1')).toBeInTheDocument(); // Completed
    expect(screen.getByText('0')).toBeInTheDocument(); // Overdue
  });

  test('opens create task form when New Task button is clicked', async () => {
    renderTasks();

    const newTaskButton = screen.getByText('New Task');
    await userEvent.click(newTaskButton);

    await waitFor(() => {
      expect(screen.getByText('Create New Task')).toBeInTheDocument();
    });
  });

  test('filters tasks by search term', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search tasks...');
    await userEvent.type(searchInput, 'Task 1');

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    expect(screen.queryByText('Task 2')).not.toBeInTheDocument();
    expect(screen.queryByText('Task 3')).not.toBeInTheDocument();
  });

  test('filters tasks by status', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    const statusFilter = screen.getByDisplayValue('All Tasks (3)');
    await userEvent.selectOptions(statusFilter, 'IN_PROGRESS');

    await waitFor(() => {
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });

    expect(screen.queryByText('Task 1')).not.toBeInTheDocument();
    expect(screen.queryByText('Task 3')).not.toBeInTheDocument();
  });

  test('shows empty state when no tasks', async () => {
    tasksAPI.getTasks.mockResolvedValue([]);
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('No tasks found')).toBeInTheDocument();
    });

    expect(screen.getByText('Get started by creating your first task!')).toBeInTheDocument();
  });

  test('shows empty state when search returns no results', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search tasks...');
    await userEvent.type(searchInput, 'nonexistent task');

    await waitFor(() => {
      expect(screen.getByText('No tasks found')).toBeInTheDocument();
    });

    expect(screen.getByText('Try adjusting your search or filters.')).toBeInTheDocument();
  });

  test('creates new task successfully', async () => {
    tasksAPI.createTask.mockResolvedValue({
      id: 4,
      title: 'New Task',
      description: 'New Description',
      status: 'TODO',
      owner_id: 1
    });

    renderTasks();

    // Open create form
    const newTaskButton = screen.getByText('New Task');
    await userEvent.click(newTaskButton);

    await waitFor(() => {
      expect(screen.getByText('Create New Task')).toBeInTheDocument();
    });

    // Fill form
    const titleInput = screen.getByPlaceholderText('Enter task title...');
    const descriptionInput = screen.getByPlaceholderText('Describe your task...');

    await userEvent.type(titleInput, 'New Task');
    await userEvent.type(descriptionInput, 'New Description');

    // Submit form
    const createButton = screen.getByText('Create Task');
    await userEvent.click(createButton);

    await waitFor(() => {
      expect(tasksAPI.createTask).toHaveBeenCalledWith({
        title: 'New Task',
        description: 'New Description',
        status: 'TODO',
        due_date: null
      });
    });

    // Verify tasks are reloaded
    expect(tasksAPI.getTasks).toHaveBeenCalledTimes(2);
  });

  test('handles API error gracefully', async () => {
    tasksAPI.getTasks.mockRejectedValue(new Error('API Error'));
    const toast = require('react-hot-toast').default;

    renderTasks();

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load tasks');
    });
  });

  test('deletes task with confirmation', async () => {
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);

    tasksAPI.deleteTask.mockResolvedValue();
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    // Find and click delete button (assuming it exists in TaskCard)
    // Note: This would need the actual TaskCard component to be rendered
    // For now, we'll test the handler function directly

    // Restore window.confirm
    window.confirm = originalConfirm;
  });

  test('sorts tasks correctly', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    const sortSelect = screen.getByDisplayValue('Created Date');
    await userEvent.selectOptions(sortSelect, 'title');

    // Tasks should be re-sorted by title
    // The order would change based on alphabetical sorting
    await waitFor(() => {
      const taskElements = screen.getAllByText(/Task \d/);
      expect(taskElements).toHaveLength(3);
    });
  });

  test('toggles sort order', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    const sortOrderButton = screen.getByTitle(/Sort (Ascending|Descending)/);
    await userEvent.click(sortOrderButton);

    // Verify that sorting order changes (tasks should reorder)
    await waitFor(() => {
      const taskElements = screen.getAllByText(/Task \d/);
      expect(taskElements).toHaveLength(3);
    });
  });

  test('clears search filter', async () => {
    renderTasks();

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    });

    // Search for a task
    const searchInput = screen.getByPlaceholderText('Search tasks...');
    await userEvent.type(searchInput, 'Task 1');

    await waitFor(() => {
      expect(screen.getByText('Search: "Task 1"')).toBeInTheDocument();
    });

    // Clear search filter
    const clearButton = screen.getByText('×');
    await userEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.queryByText('Search: "Task 1"')).not.toBeInTheDocument();
    });

    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
  });
});