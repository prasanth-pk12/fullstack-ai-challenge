import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import TaskCard from '../../components/TaskCard';

// Mock the useAuth hook
const mockUser = {
  id: 1,
  username: 'testuser',
  role: 'USER'
};

const mockAdminUser = {
  id: 2,
  username: 'admin',
  role: 'ADMIN'
};

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser
  })
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => <div>{children}</div>
}));

const mockTask = {
  id: 1,
  title: 'Test Task',
  description: 'Test Description',
  status: 'TODO',
  due_date: '2024-12-31T23:59:59Z',
  owner_id: 1,
  attachments: ['test.pdf'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

const mockTaskOtherUser = {
  ...mockTask,
  id: 2,
  owner_id: 3,
  title: 'Other User Task'
};

const renderTaskCard = (task = mockTask, props = {}) => {
  const defaultProps = {
    onEdit: jest.fn(),
    onDelete: jest.fn(),
    onStatusChange: jest.fn(),
    onViewAttachments: jest.fn(),
    ...props
  };

  return render(
    <BrowserRouter>
      <AuthProvider>
        <TaskCard task={task} {...defaultProps} />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('TaskCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders task information correctly', () => {
    renderTaskCard();

    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText(/Due:/)).toBeInTheDocument();
    expect(screen.getByText(/1 file/)).toBeInTheDocument();
  });

  test('shows edit and delete buttons for task owner', () => {
    renderTaskCard();

    expect(screen.getByTitle('Edit task')).toBeInTheDocument();
    expect(screen.getByTitle('Delete task')).toBeInTheDocument();
  });

  test('hides delete button for non-owners (non-admin)', () => {
    renderTaskCard(mockTaskOtherUser);

    expect(screen.queryByTitle('Edit task')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Delete task')).not.toBeInTheDocument();
  });

  test('shows status quick action buttons for task owner', () => {
    renderTaskCard();

    expect(screen.getByText('TODO')).toBeInTheDocument();
    expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
    expect(screen.getByText('DONE')).toBeInTheDocument();
  });

  test('calls onEdit when edit button is clicked', async () => {
    const onEdit = jest.fn();
    renderTaskCard(mockTask, { onEdit });

    const editButton = screen.getByTitle('Edit task');
    await userEvent.click(editButton);

    expect(onEdit).toHaveBeenCalledWith(mockTask);
  });

  test('calls onDelete when delete button is clicked', async () => {
    const onDelete = jest.fn();
    renderTaskCard(mockTask, { onDelete });

    const deleteButton = screen.getByTitle('Delete task');
    await userEvent.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith(mockTask.id);
  });

  test('calls onStatusChange when status button is clicked', async () => {
    const onStatusChange = jest.fn();
    renderTaskCard(mockTask, { onStatusChange });

    const inProgressButton = screen.getByText('IN PROGRESS');
    await userEvent.click(inProgressButton);

    expect(onStatusChange).toHaveBeenCalledWith(mockTask.id, 'IN_PROGRESS');
  });

  test('calls onViewAttachments when attachments are clicked', async () => {
    const onViewAttachments = jest.fn();
    renderTaskCard(mockTask, { onViewAttachments });

    const attachmentButton = screen.getByText(/1 file/);
    await userEvent.click(attachmentButton);

    expect(onViewAttachments).toHaveBeenCalledWith(mockTask);
  });

  test('displays overdue indicator for overdue tasks', () => {
    const overdueTask = {
      ...mockTask,
      due_date: '2020-01-01T00:00:00Z', // Past date
      status: 'TODO'
    };

    renderTaskCard(overdueTask);

    expect(screen.getByText('(Overdue)')).toBeInTheDocument();
  });

  test('does not show overdue indicator for completed tasks', () => {
    const completedTask = {
      ...mockTask,
      due_date: '2020-01-01T00:00:00Z', // Past date
      status: 'DONE'
    };

    renderTaskCard(completedTask);

    expect(screen.queryByText('(Overdue)')).not.toBeInTheDocument();
  });

  test('disables status change buttons during update', async () => {
    const onStatusChange = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    renderTaskCard(mockTask, { onStatusChange });

    const inProgressButton = screen.getByText('IN PROGRESS');
    await userEvent.click(inProgressButton);

    // Button should be disabled during update
    expect(inProgressButton).toHaveClass('opacity-50');
    expect(inProgressButton).toHaveClass('cursor-not-allowed');
  });
});

// Admin user tests
describe('TaskCard Component - Admin User', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock admin user
    require('../../contexts/AuthContext').useAuth.mockReturnValue({
      user: mockAdminUser
    });
  });

  test('admin can see edit and delete buttons for any task', () => {
    renderTaskCard(mockTaskOtherUser);

    expect(screen.getByTitle('Edit task')).toBeInTheDocument();
    expect(screen.getByTitle('Delete task')).toBeInTheDocument();
  });

  test('admin can change status of any task', () => {
    renderTaskCard(mockTaskOtherUser);

    expect(screen.getByText('TODO')).toBeInTheDocument();
    expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
    expect(screen.getByText('DONE')).toBeInTheDocument();
  });
});