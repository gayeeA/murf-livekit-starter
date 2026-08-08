'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { ConnectionState } from 'livekit-client';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { CallEndedView } from '@/components/app/call-ended-view';
import { ConnectingView } from '@/components/app/connecting-view';
import type { MicPermissionErrorKind } from '@/components/app/mic-permission-notice';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionConnectingView = motion.create(ConnectingView);
const MotionCallEndedView = motion.create(CallEndedView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

function getMicErrorKind(error: unknown): MicPermissionErrorKind {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      return 'denied';
    }
    if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      return 'no-device';
    }
  }
  return 'unknown';
}

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, connectionState, start } = useSessionContext();
  const { resolvedTheme } = useTheme();

  const [micError, setMicError] = useState<MicPermissionErrorKind | null>(null);
  const hasConnectedRef = useRef(false);
  const [hasEnded, setHasEnded] = useState(false);

  useEffect(() => {
    if (isConnected) {
      hasConnectedRef.current = true;
      setHasEnded(false);
    } else if (connectionState === ConnectionState.Disconnected && hasConnectedRef.current) {
      setHasEnded(true);
    }
  }, [isConnected, connectionState]);

  const handleStartCall = useCallback(async () => {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
    } catch (error) {
      setMicError(getMicErrorKind(error));
      return;
    }

    setHasEnded(false);
    start();
  }, [start]);

  const handleDeviceError = useCallback(({ error }: { source: unknown; error: Error }) => {
    setMicError(getMicErrorKind(error));
  }, []);

  const isConnecting = !isConnected && connectionState === ConnectionState.Connecting;
  const showCallEnded = !isConnected && !isConnecting && hasEnded;
  const showWelcome = !isConnected && !isConnecting && !hasEnded;

  return (
    <AnimatePresence mode="wait">
      {/* Ready */}
      {showWelcome && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
          micError={micError}
        />
      )}
      {/* Connecting */}
      {isConnecting && <MotionConnectingView key="connecting" {...VIEW_MOTION_PROPS} />}
      {/* Call ended */}
      {showCallEnded && (
        <MotionCallEndedView
          key="call-ended"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
        />
      )}
      {/* Session view (Listening / Speaking) */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          onDeviceError={handleDeviceError}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
