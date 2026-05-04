import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LogisticsStatusCard } from './LogisticsStatusCard';
import { LogisticsStatus } from '../../types';

const mockData: LogisticsStatus = {
  status: 'yellow',
  critical_tasks: ['laundry', 'grocery run'],
  tasks_with_steps: [
    {
      name: 'laundry',
      status: 'pending',
      days_overdue: 3,
      priority: 'high',
      subtasks: ['Sort clothes', 'Run wash', 'Fold'],
      completed_subtasks: ['Sort clothes'],
      notes: null,
    },
  ],
  outsourcing_suggestions: ['Hire TaskRabbit for grocery run.'],
  time_to_resolve_minutes: 90,
};

describe('LogisticsStatusCard', () => {
  it('renders no-data state when data is null', () => {
    render(<LogisticsStatusCard data={null} />);
    expect(screen.getByText('Logistics Fixer')).toBeInTheDocument();
    expect(screen.getByText(/mention domestic tasks/i)).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<LogisticsStatusCard data={null} isLoading={true} />);
    expect(screen.queryByText('Logistics Fixer')).not.toBeInTheDocument();
  });

  it('renders critical task count and resolve time', () => {
    render(<LogisticsStatusCard data={mockData} />);
    // 2 critical tasks
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('90m')).toBeInTheDocument();
  });

  it('renders active blocker badges for critical tasks', () => {
    render(<LogisticsStatusCard data={mockData} />);
    // "laundry" appears in both the blocker badge and the task progress section
    expect(screen.getAllByText('laundry').length).toBeGreaterThan(0);
    expect(screen.getByText('grocery run')).toBeInTheDocument();
  });

  it('renders task progress section', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.getByText('Task Progress')).toBeInTheDocument();
    expect(screen.getByText('1/3 steps')).toBeInTheDocument();
  });

  it('renders outsourcing ROI suggestions', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.getByText('Hire TaskRabbit for grocery run.')).toBeInTheDocument();
    expect(screen.getByText('Outsourcing ROI')).toBeInTheDocument();
  });

  it('renders green nominal message when status is green', () => {
    const greenData: LogisticsStatus = {
      ...mockData,
      status: 'green',
      critical_tasks: [],
      tasks_with_steps: [],
      outsourcing_suggestions: [],
    };
    render(<LogisticsStatusCard data={greenData} />);
    expect(screen.getByText(/all logistical systems nominal/i)).toBeInTheDocument();
  });

  it('renders error message when provided', () => {
    const withError: LogisticsStatus = { ...mockData, error_message: 'Parser failed' };
    render(<LogisticsStatusCard data={withError} />);
    expect(screen.getByText('Parser failed')).toBeInTheDocument();
  });

  it('task progress bar has progressbar role with ARIA value attributes', () => {
    render(<LogisticsStatusCard data={mockData} />);
    const progressbar = screen.getByRole('progressbar', { name: /laundry progress/i });
    expect(progressbar).toBeInTheDocument();
    // 1 of 3 subtasks complete → Math.round(1/3 * 100) = 33
    expect(progressbar).toHaveAttribute('aria-valuenow', '33');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('progress bar uses green class when task status is completed', () => {
    const dataWithCompletedTask: LogisticsStatus = {
      ...mockData,
      tasks_with_steps: [
        {
          name: 'laundry',
          status: 'completed',
          days_overdue: 0,
          priority: 'low',
          subtasks: ['Sort clothes', 'Wash', 'Fold'],
          completed_subtasks: ['Sort clothes', 'Wash', 'Fold'],
          notes: null,
        },
      ],
    };
    const { container } = render(<LogisticsStatusCard data={dataWithCompletedTask} />);
    const bar = container.querySelector('.bg-status-green');
    expect(bar).not.toBeNull();
  });

  it('progressbar aria-valuenow is 0 when task has empty subtasks', () => {
    const dataWithNoSubtasks: LogisticsStatus = {
      ...mockData,
      tasks_with_steps: [
        {
          name: 'grocery run',
          status: 'pending',
          days_overdue: 1,
          priority: 'medium',
          subtasks: [],
          completed_subtasks: [],
          notes: null,
        },
      ],
    };
    render(<LogisticsStatusCard data={dataWithNoSubtasks} />);
    const progressbar = screen.getByRole('progressbar', { name: /grocery run progress/i });
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
  });

  it('does not render N/0 steps when subtasks empty but completed_subtasks nonempty', () => {
    const corruptData: LogisticsStatus = {
      ...mockData,
      tasks_with_steps: [
        {
          name: 'laundry',
          status: 'pending',
          days_overdue: 1,
          priority: 'medium',
          subtasks: [],
          completed_subtasks: ['sort', 'wash', 'dry'],
          notes: null,
        },
      ],
    };
    render(<LogisticsStatusCard data={corruptData} />);
    expect(screen.queryByText(/3\/0 steps/i)).toBeNull();
    expect(screen.queryByText(/\/0 steps/i)).toBeNull();
  });

  it('renders correct fraction when both subtask lists are nonempty', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.getByText('1/3 steps')).toBeInTheDocument();
  });

  it('renders nothing for steps count when both subtask lists are empty', () => {
    const noSubtaskData: LogisticsStatus = {
      ...mockData,
      tasks_with_steps: [
        {
          name: 'quarterly report',
          status: 'pending',
          days_overdue: 2,
          priority: 'high',
          subtasks: [],
          completed_subtasks: [],
          notes: null,
        },
      ],
    };
    render(<LogisticsStatusCard data={noSubtaskData} />);
    expect(screen.queryByText(/steps/i)).toBeNull();
  });

  it('renders no checkbox buttons when onCompleteSubtask is not provided', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.queryAllByRole('checkbox')).toHaveLength(0);
  });

  it('renders a checkbox button per subtask when onCompleteSubtask is provided', () => {
    const handler = vi.fn();
    render(<LogisticsStatusCard data={mockData} onCompleteSubtask={handler} />);
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(3); // mockData has 3 subtasks
  });

  it('completed subtask checkbox has aria-checked true', () => {
    const handler = vi.fn();
    render(<LogisticsStatusCard data={mockData} onCompleteSubtask={handler} />);
    const checkedBoxes = screen
      .getAllByRole('checkbox')
      .filter((el) => el.getAttribute('aria-checked') === 'true');
    expect(checkedBoxes).toHaveLength(1); // mockData has 1 completed subtask
  });

  it('clicking an uncompleted subtask calls onCompleteSubtask', () => {
    const handler = vi.fn().mockResolvedValue(undefined);
    render(<LogisticsStatusCard data={mockData} onCompleteSubtask={handler} />);
    const unchecked = screen
      .getAllByRole('checkbox')
      .find((el) => el.getAttribute('aria-checked') === 'false');
    expect(unchecked).toBeDefined();
    fireEvent.click(unchecked!);
    expect(handler).toHaveBeenCalledWith('laundry', expect.any(String));
  });

  it('clicking a completed subtask does not call onCompleteSubtask', () => {
    const handler = vi.fn();
    render(<LogisticsStatusCard data={mockData} onCompleteSubtask={handler} />);
    const checked = screen
      .getAllByRole('checkbox')
      .find((el) => el.getAttribute('aria-checked') === 'true');
    expect(checked).toBeDefined();
    fireEvent.click(checked!);
    expect(handler).not.toHaveBeenCalled();
  });

  it('optimistic check appears immediately on click before API resolves', () => {
    let resolveClick!: () => void;
    const handler = vi.fn().mockReturnValue(
      new Promise<void>((res) => {
        resolveClick = res;
      })
    );
    render(<LogisticsStatusCard data={mockData} onCompleteSubtask={handler} />);

    const unchecked = screen
      .getAllByRole('checkbox')
      .find((el) => el.getAttribute('aria-checked') === 'false');
    expect(unchecked).toBeDefined();

    fireEvent.click(unchecked!);
    // Optimistic state: the clicked box should now show aria-checked="true"
    expect(unchecked!.getAttribute('aria-checked')).toBe('true');

    resolveClick();
  });
});
