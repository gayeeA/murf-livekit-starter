import { Loader } from 'lucide-react';

export const ConnectingView = ({ ref }: React.ComponentProps<'div'>) => {
  return (
    <div ref={ref}>
      <section className="flex flex-col items-center justify-center px-6 text-center">
        <div className="border-border/60 bg-card/90 flex w-full max-w-sm flex-col items-center rounded-3xl border p-8 shadow-xl backdrop-blur-sm">
          <div className="from-primary to-accent mb-4 flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg">
            <Loader className="size-6 animate-spin text-white" />
          </div>
          <p className="text-foreground text-lg font-semibold">Connecting you to Pooja…</p>
          <p className="text-muted-foreground mt-1.5 max-w-xs text-sm leading-6">
            Please wait a moment while we set up a secure line.
          </p>
        </div>
      </section>
    </div>
  );
};
