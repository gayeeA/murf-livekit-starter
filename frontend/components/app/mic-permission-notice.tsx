import { MicrophoneSlashIcon } from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/ui/button';

export type MicPermissionErrorKind = 'denied' | 'no-device' | 'unknown';

interface MicPermissionNoticeProps {
  kind: MicPermissionErrorKind;
  onRetry: () => void;
}

const COPY: Record<MicPermissionErrorKind, { title: string; description: string }> = {
  denied: {
    title: 'Microphone access is blocked',
    description:
      "Pooja needs your microphone to hear you. Click the lock/site-info icon in your browser's address bar, allow Microphone access, then try again.",
  },
  'no-device': {
    title: 'No microphone found',
    description:
      'We could not detect a microphone on this device. Please connect a microphone or check your system audio settings, then try again.',
  },
  unknown: {
    title: "Couldn't access your microphone",
    description:
      'Something went wrong while requesting microphone access. Please check your device settings and try again.',
  },
};

export function MicPermissionNotice({ kind, onRetry }: MicPermissionNoticeProps) {
  const { title, description } = COPY[kind];

  return (
    <div
      role="alert"
      className="border-destructive/30 bg-destructive/5 mt-6 flex w-full max-w-sm flex-col items-center gap-2 rounded-xl border p-4 text-center"
    >
      <MicrophoneSlashIcon weight="bold" className="text-destructive size-6" />
      <p className="text-foreground text-sm font-semibold">{title}</p>
      <p className="text-muted-foreground text-xs leading-5">{description}</p>
      <Button size="sm" variant="outline" onClick={onRetry} className="mt-1 rounded-full">
        Try again
      </Button>
    </div>
  );
}
