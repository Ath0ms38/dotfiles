// Type definitions for AGS v2 global modules

declare module 'resource:///com/github/Aylur/ags' {
  export * from 'ags';
}

declare module 'resource:///com/github/Aylur/ags/widget.js' {
  export * from 'ags/widget';
}

declare module 'resource:///com/github/Aylur/ags/service.js' {
  export * from 'ags/service';
}

declare module 'resource:///com/github/Aylur/ags/utils.js' {
  export * from 'ags/utils';
}

declare module 'resource:///com/github/Aylur/ags/app.js' {
  export * from 'ags/app';
}

declare module 'resource:///com/github/Aylur/ags/variable.js' {
  export * from 'ags/variable';
}

declare module 'resource:///com/github/Aylur/ags/animation.js' {
  export * from 'ags/animation';
}
declare module "astal" {
  export function Variable<T = any>(initial: T): {
    get(): T;
    set(val: T): void;
    poll(interval: number, fn: () => Promise<T> | T): any;
  };
  export function bind(...args: any[]): any;
}
declare module "astal/gtk3" {
  export const Widget: any;
  export const App: any;
  export const Gtk: any;
}
declare module "astal/process" {
  export const execAsync: any;
  export const exec: any;
}
declare module "gi://AstalWp" {
  const Wp: any;
  export default Wp;
}
declare module "gi://AstalMpris" {
  const Mpris: any;
  export default Mpris;
}
declare module "gi://AstalNetwork" {
  const Network: any;
  export default Network;
}
declare module "gi://AstalBluetooth" {
  const Bluetooth: any;
  export default Bluetooth;
}
declare module "gi://AstalNotifd" {
  const Notifd: any;
  export default Notifd;
}
declare module "gi://AstalBattery" {
  const Battery: any;
  export default Battery;
}
declare module "./jsx/jsx-runtime" {
  export function jsx(type: any, props: any): any;
  export { jsx as jsxs, jsx as jsxDEV };
}