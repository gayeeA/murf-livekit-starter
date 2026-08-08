import { CheckCircleIcon } from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/ui/button';

interface CallEndedViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const CallEndedView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & CallEndedViewProps) => {
  return (
    <div ref={ref}>
      <section className="flex flex-col items-center justify-center px-6 text-center">
        <div className="border-border/60 bg-card/90 flex w-full max-w-sm flex-col items-center rounded-3xl border p-8 shadow-xl backdrop-blur-sm">
          <div className="from-primary to-accent mb-4 flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg">
            <CheckCircleIcon weight="fill" className="size-7 text-white" />
          </div>

          <h1 className="text-foreground text-lg font-semibold">Call ended</h1>
          <p className="text-muted-foreground mt-1.5 max-w-xs text-sm leading-6">
            Your conversation with Pooja has ended. Your details were not saved anywhere.
          </p>

          <Button
            size="lg"
            onClick={onStartCall}
            className="mt-6 w-full rounded-full font-mono text-xs font-bold tracking-wider uppercase shadow-md"
          >
            {startButtonText}
          </Button>
        </div>
      </section>
    </div>
  );
};
