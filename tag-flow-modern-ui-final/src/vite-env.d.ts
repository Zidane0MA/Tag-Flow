/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_HOST: string;
  readonly VITE_BACKEND_PORT: string;
  readonly VITE_API_URL: string;
  // más variables de entorno según sea necesario
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}