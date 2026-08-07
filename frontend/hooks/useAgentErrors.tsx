import { ReactNode, useEffect, useRef } from 'react';
import { toast as sonnerToast } from 'sonner';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ToastProps {
  title: ReactNode;
  description: ReactNode;
}

function toastAlert(toast: ToastProps) {
  const { title, description } = toast;

  return sonnerToast.custom(
    (id) => (
      <Alert onClick={() => sonnerToast.dismiss(id)} className="bg-accent w-full md:w-[364px]">
        <WarningIcon weight="bold" />
        <AlertTitle>{title}</AlertTitle>
        {description && <AlertDescription>{description}</AlertDescription>}
      </Alert>
    ),
    { duration: 10_000 }
  );
}

export function useAgentErrors() {
  const agent = useAgent();
  const { isConnected } = useSessionContext();
  const hasShownFailureToast = useRef(false);

  useEffect(() => {
    if (!isConnected || agent.state !== 'failed') {
      hasShownFailureToast.current = false;
      return;
    }

    if (hasShownFailureToast.current) {
      return;
    }

    hasShownFailureToast.current = true;

    const reasons = Array.isArray(agent.failureReasons) ? agent.failureReasons : [];
    const hasMultipleReasons = reasons.length > 1;
    const hasSingleReason = reasons.length === 1;

    toastAlert({
      title: 'Agent connection issue',
      description: (
        <>
          {hasMultipleReasons && (
            <ul className="list-inside list-disc">
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
          {hasSingleReason && <p className="w-full">{reasons[0]}</p>}
          {!hasMultipleReasons && !hasSingleReason && (
            <p className="w-full">The voice agent stopped unexpectedly. Please try reconnecting.</p>
          )}
          <p className="w-full">
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://docs.livekit.io/agents/start/voice-ai/"
              className="whitespace-nowrap underline"
            >
              See quickstart guide
            </a>
            .
          </p>
        </>
      ),
    });
  }, [agent, isConnected]);
}
