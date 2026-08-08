import { ShieldCheckIcon } from '@phosphor-icons/react/dist/ssr';
import {
  type MicPermissionErrorKind,
  MicPermissionNotice,
} from '@/components/app/mic-permission-notice';
import { Button } from '@/components/ui/button';

const TOPICS = ['Savings', 'Loans', 'Insurance', 'Cards'];

function WelcomeImage() {
  return (
    <div className="from-primary to-accent mb-5 flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg">
      <svg
        width="30"
        height="30"
        viewBox="0 0 30 30"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M9 8h13M9 12h13M9 8c0 0 10 0 10 5.5S9 24 9 24l11 5"
          stroke="white"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  micError?: MicPermissionErrorKind | null;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  micError,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref}>
      <section className="flex flex-col items-center justify-center px-6 text-center">
        <div className="border-border/60 bg-card/90 flex w-full max-w-sm flex-col items-center rounded-3xl border p-8 shadow-xl backdrop-blur-sm">
          <WelcomeImage />

          <h1 className="text-foreground text-2xl font-semibold tracking-tight">Pooja</h1>
          <p className="text-muted-foreground mt-1.5 max-w-xs text-sm leading-6 font-medium">
            Your voice helpline for savings, loans, insurance &amp; more — talk to me anytime, in
            English or Telugu.
          </p>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
            {TOPICS.map((topic) => (
              <span
                key={topic}
                className="bg-muted text-muted-foreground rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase"
              >
                {topic}
              </span>
            ))}
          </div>

          <Button
            size="lg"
            onClick={onStartCall}
            className="mt-6 w-full rounded-full font-mono text-xs font-bold tracking-wider uppercase shadow-md"
          >
            {startButtonText}
          </Button>

          {micError && <MicPermissionNotice kind={micError} onRetry={onStartCall} />}

          <div className="text-muted-foreground mt-5 flex items-center gap-1.5 text-xs">
            <ShieldCheckIcon weight="bold" className="text-primary size-3.5" />
            Your call is private. No financial details are stored.
          </div>
        </div>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Powered by Murf Falcon TTS · Part of{' '}
          <span className="font-semibold">10 Days of Voice Agents</span> · #VoiceForBharat
        </p>
      </div>
    </div>
  );
};
