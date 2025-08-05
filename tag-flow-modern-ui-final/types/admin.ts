
export enum OperationStatus {
  RUNNING = 'Running',
  COMPLETED = 'Completed',
  FAILED = 'Failed',
  CANCELLED = 'Cancelled',
  PENDING = 'Pending',
}

export enum OperationType {
  // Video
  PROCESS_VIDEOS = 'Procesar Videos',
  ANALYZE_VIDEOS = 'Reanalizar Videos',
  // Database
  POPULATE_DB = 'Poblar BD',
  OPTIMIZE_DB = 'Optimizar BD',
  CLEAR_DB = 'Limpiar BD',
  // Thumbnails
  POPULATE_THUMBNAILS = 'Poblar Thumbnails',
  REGENERATE_THUMBNAILS = 'Regenerar Thumbnails',
  CLEAN_THUMBNAILS = 'Limpiar Huérfanos',
  THUMBNAIL_STATS = 'Estadísticas de Thumbnails',
  // System
  BACKUP = 'Crear Backup',
  VERIFY_SYSTEM = 'Verificar Sistema',
  VERIFY_FILES = 'Verificar Archivos',
  INTEGRITY_REPORT = 'Reporte de Integridad',
  LIST_BACKUPS = 'Listar Backups',
  CLEANUP_BACKUPS = 'Limpiar Backups',
  // Character
  CLEAN_FALSE_POSITIVES = 'Limpiar Falsos Positivos',
  UPDATE_CREATOR_MAPPINGS = 'Actualizar Mapeos de Creador',
  ANALYZE_TITLES = 'Analizar Títulos',
  DOWNLOAD_CHARACTER_IMAGES = 'Descargar Imágenes de Personajes',
  CHARACTER_DETECTION_REPORT = 'Reporte de Detección',
  // Generic
  EMPTY_TRASH = 'Vaciar Papelera',
  RESET_DB = 'Reset Completo BD',
}

export interface Operation {
  id: string;
  type: OperationType;
  status: OperationStatus;
  progress: number;
  message: string;
  startTime: string;
  endTime?: string;
  logs: string[];
  command: string;
  parameters: Record<string, any>;
}

export interface SystemHealth {
  status: 'good' | 'warning' | 'error';
  message: string;
}

export interface Character {
    id: string;
    name: string; // canonical_name
    game: string;
    variants: {
      exact: string[];
      joined: string[];
      native: string[];
      common: string[];
    };
    contextHints: string[];
    detectionWeight: number;
    priority: number;
    videoCount: number;
}

export interface AdminStats {
    totalPosts: number;
    activeOperations: number;
    pendingVideos: number;
    diskUsage: number;
    diskTotal: number;
    systemHealth: SystemHealth;
    totalCharacters: number;
    totalGames: number;
    configuredApis: number;
    configuredPaths: number;
}

export interface AdminConfig {
    apiKeys: {
        youtube: string;
        spotifyClientId: string;
        spotifyClientSecret: string;
        googleCredentialsPath: string;
        acrcloudHost: string;
        acrcloudAccessKey: string;
        acrcloudAccessSecret: string;
    };
    paths: {
        youtubeDb: string;
        tiktokDb: string;
        instagramDb: string;
        organizedBasePath: string;
    };
    settings: {
        maxConcurrentProcessing: number;
        thumbnailSize: string;
        thumbnailMode: 'ultra_fast' | 'balanced' | 'quality' | 'gpu' | 'auto';
        useOptimizedDatabase: boolean;
        databaseCacheTTL: number;
        databaseCacheSize: number;
        enablePerformanceMetrics: boolean;
        useGPUDeepFace: boolean;
        deepFaceModel: 'ArcFace' | 'VGG-Face' | 'Facenet' | 'OpenFace';
    }
}

export interface AdminContextType {
    stats: AdminStats;
    operations: Operation[];
    characters: Character[];
    config: AdminConfig;
    games: string[];
    startOperation: (type: OperationType, params?: Record<string, any>) => void;
    cancelOperation: (id: string) => void;
    updateCharacter: (character: Character) => void;
    addCharacter: (character: Omit<Character, 'id' | 'videoCount'>) => void;
    deleteCharacter: (id: string) => void;
    updateConfig: (newConfig: Partial<AdminConfig>) => void;
    addGame: (gameName: string) => void;
}
