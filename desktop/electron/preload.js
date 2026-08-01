const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('wren', {
  platform: process.platform,
  isElectron: true,
  version: '1.0.0',
});
