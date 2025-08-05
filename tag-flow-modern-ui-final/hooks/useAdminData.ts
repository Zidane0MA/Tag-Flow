
import React, { createContext, useState, useContext, useCallback, useMemo, useEffect } from 'react';
import { AdminContextType, Operation, OperationStatus, OperationType, Character, AdminStats, AdminConfig } from '../types/admin';
import { useData } from './useMockData';

const AdminContext = createContext<AdminContextType | null>(null);

const MOCK_CHARACTERS: Character[] = [
    { id: 'char_1', name: 'Gawr Gura', game: 'Hololive', variants: { exact: ['gawr gura'], joined: ['gawrgura'], native: ['がうる・ぐら'], common: ['gura', 'goomba'] }, contextHints: ['vtuber', 'english'], detectionWeight: 0.9, priority: 5, videoCount: 15 },
    { id: 'char_2', name: 'Hatsune Miku', game: 'Vocaloid', variants: { exact: ['hatsune miku'], joined: ['hatsunemiku'], native: ['初音ミク'], common: ['miku'] }, contextHints: ['vocaloid', 'diva'], detectionWeight: 0.95, priority: 5, videoCount: 22 },
    { id: 'char_3', name: 'Zhongli', game: 'Genshin Impact', variants: { exact: ['zhongli'], joined: [], native: ['鍾離'], common: ['rex lapis'] }, contextHints: ['geo', 'archon'], detectionWeight: 0.8, priority: 4, videoCount: 8 },
];

const MOCK_GAMES = ['Hololive', 'Vocaloid', 'Genshin Impact', 'Nijisanji', 'Star Rail'];

const buildCommandString = (type: OperationType, params: Record<string, any>): string => {
    const typeMap: Record<OperationType, string> = {
        [OperationType.PROCESS_VIDEOS]: 'process',
        [OperationType.ANALYZE_VIDEOS]: 'process --reanalyze',
        [OperationType.POPULATE_DB]: 'populate-db',
        [OperationType.OPTIMIZE_DB]: 'optimize-db',
        [OperationType.CLEAR_DB]: 'clear-db',
        [OperationType.POPULATE_THUMBNAILS]: 'populate-thumbnails',
        [OperationType.REGENERATE_THUMBNAILS]: 'regenerate-thumbnails',
        [OperationType.CLEAN_THUMBNAILS]: 'clean-thumbnails',
        [OperationType.THUMBNAIL_STATS]: 'thumbnail-stats',
        [OperationType.BACKUP]: 'backup',
        [OperationType.VERIFY_SYSTEM]: 'verify',
        [OperationType.VERIFY_FILES]: 'verify-files',
        [OperationType.INTEGRITY_REPORT]: 'integrity-report',
        [OperationType.LIST_BACKUPS]: 'list-backups',
        [OperationType.CLEANUP_BACKUPS]: 'cleanup-backups',
        [OperationType.CLEAN_FALSE_POSITIVES]: 'clean-false-positives',
        [OperationType.UPDATE_CREATOR_MAPPINGS]: 'update-creator-mappings',
        [OperationType.ANALYZE_TITLES]: 'analyze-titles',
        [OperationType.DOWNLOAD_CHARACTER_IMAGES]: 'download-character-images',
        [OperationType.CHARACTER_DETECTION_REPORT]: 'character-detection-report',
        [OperationType.EMPTY_TRASH]: 'empty-trash',
        [OperationType.RESET_DB]: 'reset-database',
    };
    const command = typeMap[type] || 'unknown-command';
    const args = Object.entries(params)
        .map(([key, value]) => {
            if (typeof value === 'boolean' && value) return `--${key}`;
            if (typeof value !== 'boolean' && value !== undefined && value !== '') return `--${key} ${value}`;
            return '';
        })
        .filter(Boolean)
        .join(' ');

    return `main.py ${command} ${args}`;
};

export const AdminProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { getStats: getMainStats } = useData();
    const [operations, setOperations] = useState<Operation[]>([]);
    const [characters, setCharacters] = useState<Character[]>(MOCK_CHARACTERS);
    const [games, setGames] = useState<string[]>(MOCK_GAMES);
    const [config, setConfig] = useState<AdminConfig>({
        apiKeys: { 
            youtube: 'AIzaSy...saved', 
            spotifyClientId: '...',
            spotifyClientSecret: '...',
            googleCredentialsPath: '',
            acrcloudHost: '',
            acrcloudAccessKey: '',
            acrcloudAccessSecret: '',
        },
        paths: { 
            youtubeDb: '/data/db/youtube.db', 
            tiktokDb: '/data/db/tiktok.db',
            instagramDb: '',
            organizedBasePath: '/data/organized_videos',
        },
        settings: { 
            maxConcurrentProcessing: 4, 
            thumbnailSize: '320x180',
            thumbnailMode: 'balanced',
            useOptimizedDatabase: true,
            databaseCacheTTL: 3600,
            databaseCacheSize: 1024,
            enablePerformanceMetrics: false,
            useGPUDeepFace: true,
            deepFaceModel: 'VGG-Face'
        }
    });

    const startOperation = useCallback((type: OperationType, params: Record<string, any> = {}) => {
        const newOp: Operation = {
            id: `op_${Date.now()}`,
            type,
            status: OperationStatus.RUNNING,
            progress: 0,
            message: `Iniciando ${type}...`,
            startTime: new Date().toISOString(),
            logs: [`[${new Date().toLocaleTimeString()}] Operación iniciada.`],
            parameters: params,
            command: buildCommandString(type, params),
        };
        setOperations(prev => [newOp, ...prev]);
    }, []);

    const cancelOperation = useCallback((id: string) => {
        setOperations(prev => prev.map(op => op.id === id ? { ...op, status: OperationStatus.CANCELLED, endTime: new Date().toISOString(), message: 'Cancelado por el usuario' } : op));
    }, []);
    
    useEffect(() => {
        const interval = setInterval(() => {
            setOperations(prevOps => {
                let hasChanged = false;
                const updatedOps = prevOps.map(op => {
                    if (op.status === OperationStatus.RUNNING && op.progress < 100) {
                        hasChanged = true;
                        const newProgress = Math.min(op.progress + (Math.random() * 15 + 5), 100);
                        const newLog = `[${new Date().toLocaleTimeString()}] Progreso: ${newProgress.toFixed(0)}%`;
                        const updatedOp = {
                            ...op,
                            progress: newProgress,
                            message: `Procesando... ${newProgress.toFixed(0)}%`,
                            logs: [...op.logs, newLog],
                        };
                        if (newProgress >= 100) {
                            updatedOp.status = OperationStatus.COMPLETED;
                            updatedOp.endTime = new Date().toISOString();
                            updatedOp.message = 'Completado exitosamente';
                            updatedOp.logs.push(`[${new Date().toLocaleTimeString()}] Operación completada.`);
                        }
                        return updatedOp;
                    }
                    return op;
                });
                return hasChanged ? updatedOps : prevOps;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const addCharacter = useCallback((character: Omit<Character, 'id' | 'videoCount'>) => {
        const newChar: Character = {
            ...character,
            id: `char_${Date.now()}`,
            videoCount: 0,
        };
        setCharacters(prev => [newChar, ...prev]);
    }, []);

    const updateCharacter = useCallback((character: Character) => {
        setCharacters(prev => prev.map(c => c.id === character.id ? character : c));
    }, []);
    
    const deleteCharacter = useCallback((id: string) => {
        setCharacters(prev => prev.filter(c => c.id !== id));
    }, []);

    const updateConfig = (newConfig: Partial<AdminConfig>) => {
        setConfig(prev => ({...prev, ...newConfig}));
    };
    
    const addGame = (gameName: string) => {
        if (gameName && !games.includes(gameName)) {
            setGames(prev => [...prev, gameName]);
        }
    };

    const stats: AdminStats = useMemo(() => {
        const mainStats = getMainStats();
        return {
            totalPosts: mainStats.total,
            pendingVideos: mainStats.pending,
            activeOperations: operations.filter(op => op.status === OperationStatus.RUNNING).length,
            diskUsage: 78.5,
            diskTotal: 256,
            systemHealth: { status: 'good', message: 'Todos los sistemas operativos.' },
            totalCharacters: characters.length,
            totalGames: new Set(characters.map(c => c.game)).size,
            configuredApis: Object.values(config.apiKeys).filter(k => k && k !== '...').length,
            configuredPaths: Object.values(config.paths).filter(p => p).length,
        };
    }, [getMainStats, operations, characters, config]);
    
    const distinctGames = useMemo(() => [...new Set([...games, ...characters.map(c => c.game)])], [characters, games]);

    const value = useMemo(() => ({
        stats,
        operations,
        characters,
        config,
        games: distinctGames,
        startOperation,
        cancelOperation,
        addCharacter,
        updateCharacter,
        deleteCharacter,
        updateConfig,
        addGame
    }), [stats, operations, characters, config, distinctGames, startOperation, cancelOperation, addCharacter, updateCharacter, deleteCharacter, updateConfig, addGame]);

    return React.createElement(AdminContext.Provider, { value: value }, children);
};

export const useAdminData = (): AdminContextType => {
    const context = useContext(AdminContext);
    if (!context) {
        throw new Error('useAdminData must be used within an AdminProvider');
    }
    return context;
};
