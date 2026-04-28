import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatPanel, Message } from './index';

const noop = vi.fn();

beforeEach(() => {
  noop.mockClear();
});

describe('ChatPanel', () => {
  it('renders the textarea and send button', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    expect(screen.getByPlaceholderText(/what's your status/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('shows suggested briefs when messages list is empty', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    expect(screen.getByText('Suggested Briefs')).toBeInTheDocument();
  });

  it('calls onSendMessage when the form is submitted', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);
    expect(noop).toHaveBeenCalledWith('Slept 5 hours.');
  });

  it('submits when Enter is pressed without Shift', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Test message.' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    expect(noop).toHaveBeenCalledWith('Test message.');
  });

  it('does not submit when Shift+Enter is pressed', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Draft.' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    expect(noop).not.toHaveBeenCalled();
  });

  it('fills the textarea when a suggested prompt is clicked', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    const promptBtn = screen.getByRole('button', { name: /slept 5 hours/i });
    fireEvent.click(promptBtn);
    const textarea = screen.getByPlaceholderText<HTMLTextAreaElement>(/what's your status/i);
    expect(textarea.value).toContain('Slept 5 hours');
  });

  it('shows "Analyzing..." while loading', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={true} messages={[]} />);
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeInTheDocument();
  });

  it('renders user and system messages', () => {
    const messages: Message[] = [
      { role: 'user', content: 'Hello system.' },
      { role: 'system', content: 'Roger that.' },
    ];
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={messages} />);
    expect(screen.getByText('Hello system.')).toBeInTheDocument();
    expect(screen.getByText('Roger that.')).toBeInTheDocument();
  });

  it('shows streaming bubble with cursor when streamingContent is non-null', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={true} messages={[]} streamingContent="" />);
    expect(screen.getByTestId('streaming-cursor')).toBeInTheDocument();
  });

  it('does not show streaming cursor when streamingContent is null', () => {
    render(
      <ChatPanel onSendMessage={noop} isLoading={false} messages={[]} streamingContent={null} />
    );
    expect(screen.queryByTestId('streaming-cursor')).not.toBeInTheDocument();
  });

  it('does not show streaming cursor when streamingContent is undefined', () => {
    render(<ChatPanel onSendMessage={noop} isLoading={false} messages={[]} />);
    expect(screen.queryByTestId('streaming-cursor')).not.toBeInTheDocument();
  });

  it('displays partial streamed text in the bubble', () => {
    render(
      <ChatPanel
        onSendMessage={noop}
        isLoading={true}
        messages={[]}
        streamingContent="Hello world"
      />
    );
    expect(screen.getByText(/hello world/i)).toBeInTheDocument();
    expect(screen.getByTestId('streaming-cursor')).toBeInTheDocument();
  });
});
