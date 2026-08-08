import type { AgentState } from '@livekit/components-react';
import { cn } from '@/lib/shadcn/utils';

interface StatusCopy {
  label: string;
  dotClassName: string;
}

const STATUS_COPY: Record<string, StatusCopy> = {
  connecting: { label: 'Connecting…', dotClassName: 'bg-secondary animate-pulse' },
  'pre-connect-buffering': { label: 'Connecting…', dotClassName: 'bg-secondary animate-pulse' },
  initializing: { label: 'Getting ready…', dotClassName: 'bg-secondary animate-pulse' },
  idle: { label: 'Listening to you', dotClassName: 'bg-primary' },
  listening: { label: 'Listening to you', dotClassName: 'bg-primary' },
  thinking: { label: 'Pooja is thinking…', dotClassName: 'bg-accent animate-pulse' },
  speaking: { label: 'Pooja is speaking', dotClassName: 'bg-accent' },
  disconnected: { label: 'Disconnected', dotClassName: 'bg-muted-foreground' },
  failed: { label: 'Connection issue', dotClassName: 'bg-destructive' },
};

interface AgentStatusLabelProps {
  agentState: AgentState;
  className?: string;
}

export function AgentStatusLabel({ agentState, className }: AgentStatusLabelProps) {
  const copy = STATUS_COPY[agentState] ?? STATUS_COPY.listening;

  return (
    <div
      className={cn(
        'bg-background/80 border-border/60 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 shadow-sm backdrop-blur-sm',
        className
      )}
    >
      <span className={cn('size-2 shrink-0 rounded-full', copy.dotClassName)} />
      <span className="text-foreground text-xs font-semibold tracking-wide">{copy.label}</span>
    </div>
  );
}
