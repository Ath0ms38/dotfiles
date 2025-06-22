// Type definitions for AGS v2 - Complete and Fixed

declare module "astal" {
  export interface Variable<T = any> {
    get(): T;
    set(val: T): void;
    poll(interval: number, fn: () => Promise<T> | T): Variable<T>;
  }
  
  export function Variable<T = any>(initial: T): Variable<T>;
  export function bind<T>(variable: Variable<T>): any;
  export function bind<T>(object: any, property: string): any;
}

declare module "astal/gtk3" {
  export namespace Astal {
    enum WindowAnchor {
      LEFT = 4,
      RIGHT = 8,
      TOP = 2,
      BOTTOM = 16,
    }
    enum Exclusivity {
      NORMAL = 0,
      EXCLUSIVE = 1,
      IGNORE = 2,
    }
    enum Layer {
      BACKGROUND = 0,
      BOTTOM = 1,
      TOP = 2,
      OVERLAY = 3,
    }
    enum Keymode {
      NONE = 0,
      EXCLUSIVE = 1,
      ON_DEMAND = 2,
    }
  }
  export namespace Widget {
    interface WindowProps {
      name?: string;
      className?: string;
      visible?: boolean;
      anchor?: number;
      layer?: "background" | "bottom" | "top" | "overlay" | Astal.Layer;
      margins?: [number, number, number, number]; // top, right, bottom, left
      marginTop?: number;
      marginRight?: number;
      marginBottom?: number;
      marginLeft?: number;
      keymode?: "none" | "exclusive" | "on-demand" | Astal.Keymode;
      setup?: (self: any) => void;
      child?: any;
      exclusivity?: "normal" | "exclusive" | "ignore" | Astal.Exclusivity;
      popup?: boolean;
      monitor?: number;
    }
    
    interface BoxProps {
      className?: string;
      vertical?: boolean;
      spacing?: number;
      homogeneous?: boolean;
      children?: any[];
      child?: any;
      halign?: any;
      valign?: any;
      hexpand?: boolean;
      vexpand?: boolean;
    }
    
    interface LabelProps {
      className?: string;
      label?: string;
      markup?: string;
      halign?: any;
      valign?: any;
      hexpand?: boolean;
      vexpand?: boolean;
    }
    
    interface ButtonProps {
      className?: string;
      label?: string;
      child?: any;
      onClicked?: () => void;
      halign?: any;
      valign?: any;
    }
    
    interface IconProps {
      className?: string;
      icon?: string;
      iconSize?: number;
    }
    
    export class Window {
      constructor(props: WindowProps);
      destroy(): void;
      show(): void;
      hide(): void;
      connect(signal: string, callback: (self: any, ...args: any[]) => void): void;
      get_allocation(): { width: number; height: number };
    }
    
    export class Box {
      constructor(props: BoxProps);
    }
    
    export class Label {
      constructor(props: LabelProps);
    }
    
    export class Button {
      constructor(props: ButtonProps);
    }
    
    export class Icon {
      constructor(props: IconProps);
    }
    
    export class Entry {
      constructor(props: any);
      text: string;
    }
    
    export class Slider {
      constructor(props: any);
    }
    
    export class LevelBar {
      constructor(props: any);
    }
  }
  
  export const App: {
    start(config: {
      css?: string;
      main?(): any;
      requestHandler?(request: string, res: (response: any) => void): void;
    }): void;
    quit(): void;
  };
  
  export const Gtk: any;
}

declare module "astal/process" {
  export function execAsync(cmd: string[]): Promise<string>;
  export function exec(cmd: string[]): string;
}

// GI modules
declare module "gi://AstalWp" {
  interface AudioDevice {
    volume: number;
    mute: boolean;
    volumeIcon: string;
    set_mute(mute: boolean): void;
  }
  
  interface Audio {
    defaultSpeaker: AudioDevice | null;
    defaultMicrophone: AudioDevice | null;
  }
  
  interface Wp {
    audio: Audio | null;
  }
  
  export function get_default(): Wp;
}

declare module "gi://AstalMpris" {
  export enum PlaybackStatus {
    PLAYING = "Playing",
    PAUSED = "Paused",
    STOPPED = "Stopped"
  }
  
  export enum Loop {
    NONE = "None",
    TRACK = "Track", 
    PLAYLIST = "Playlist"
  }
  
  interface Player {
    busName: string;
    identity: string;
    title: string;
    artist: string;
    album: string;
    coverArt: string;
    position: number;
    length: number;
    volume: number;
    shuffle: boolean;
    loop: Loop;
    playbackStatus: PlaybackStatus;
    charging: boolean;
    
    playPause(): void;
    next(): void;
    previous(): void;
    disconnect(): void;
  }
  
  interface Mpris {
    players: Player[];
  }
  
  export function get_default(): Mpris;
}

declare module "gi://AstalNetwork" {
  interface AccessPoint {
    bssid: string;
    ssid: string;
    strength: number;
    secure: boolean;
    iconName: string;
  }
  
  interface Wifi {
    enabled: boolean;
    ssid: string;
    strength: number;
    iconName: string;
    accessPoints: AccessPoint[];
    scan(): void;
  }
  
  interface Network {
    wifi: Wifi | null;
  }
  
  export function get_default(): Network;
}

declare module "gi://AstalBluetooth" {
  interface Device {
    address: string;
    name: string;
    icon: string;
    connected: boolean;
    disconnect(): void;
  }
  
  interface Adapter {
    setPowered(powered: boolean): void;
    startDiscovery(): void;
  }
  
  interface Bluetooth {
    isPowered: boolean;
    devices: Device[];
    adapter: Adapter | null;
  }
  
  export function get_default(): Bluetooth;
}

declare module "gi://AstalNotifd" {
  interface Action {
    id: string;
    label: string;
  }
  
  interface Notification {
    id: number;
    appName: string;
    appIcon: string;
    summary: string;
    body: string;
    time: number;
    read: boolean;
    actions: Action[];
    dismiss(): void;
    invoke(actionId: string): void;
  }
  
  interface Notifd {
    notifications: Notification[];
    get_notifications(): Notification[];
  }
  
  export function get_default(): Notifd;
}

declare module "gi://AstalBattery" {
  interface Battery {
    percentage: number;
    charging: boolean;
    timeToEmpty: number;
    batteryIconName: string;
  }
  
  export function get_default(): Battery;
}

declare module "gi://Gtk?version=3.0" {
  export enum Align {
    FILL = 0,
    START = 1,
    END = 2,
    CENTER = 3,
    BASELINE = 4
  }
  
  export enum RevealerTransitionType {
    NONE = 0,
    CROSSFADE = 1,
    SLIDE_RIGHT = 2,
    SLIDE_LEFT = 3,
    SLIDE_UP = 4,
    SLIDE_DOWN = 5
  }
  
  const Gtk: {
    Align: typeof Align;
    RevealerTransitionType: typeof RevealerTransitionType;
  };
  
  export default Gtk;
}

// JSX Runtime
declare module "./jsx/jsx-runtime" {
  export function jsx(type: any, props: any): any;
  export { jsx as jsxs, jsx as jsxDEV };
}

// Global JSX namespace for TSX files
declare global {
  namespace JSX {
    interface IntrinsicElements {
      box: any;
      label: any;
      button: any;
      icon: any;
      entry: any;
      slider: any;
      scale: any;
      checkbox: any;
      switch: any;
      revealer: any;
      scrollable: any;
      separator: any;
      circularprogress: any;
      window: any;
    }
  }
}
