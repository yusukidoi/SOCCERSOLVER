/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_DATA_SEASON?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
