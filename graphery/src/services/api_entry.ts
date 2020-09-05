const PRO_BASE_URL = 'https://api-graphery.reedcompbio.org';
const DEV_BASE_URL = 'http://localhost:8082';
export const BASE_URL =
  process.env.NODE_ENV === 'production' ? PRO_BASE_URL : DEV_BASE_URL;

const PRO_BASE_SOCKET = 'wss://api-graphery.reedcompbio.org';
const DEV_BASE_SOCKET = 'ws://localhost:8082';
export const BASE_SOCKET =
  (process.env.NODE_ENV === 'production' ? PRO_BASE_SOCKET : DEV_BASE_SOCKET) +
  '/ws/';
