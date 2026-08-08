export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Pooja',
  pageTitle: 'Pooja — Voice Financial Helpline',
  pageDescription:
    'A Telugu-fluent financial helpline voice agent for #VoiceForBharat, powered by Murf Falcon — the fastest TTS API',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/pooja-logo.svg',
  accent: '#34aeda',
  logoDark: '/pooja-logo-dark.svg',
  accentDark: '#5cc6ec',
  startButtonText: 'Talk to Pooja',

  // audio visualization configuration — premium blue/violet bars matching the fintech theme
  audioVisualizerType: 'bar',
  audioVisualizerColor: '#34aeda',
  audioVisualizerColorDark: '#5cc6ec',
  audioVisualizerBarCount: 5,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
