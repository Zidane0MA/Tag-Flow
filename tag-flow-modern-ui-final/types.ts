
export enum PostType {
  VIDEO = 'Video',
  IMAGE = 'Image',
}

export enum Platform {
  YOUTUBE = 'YouTube',
  TIKTOK = 'TikTok',
  INSTAGRAM = 'Instagram',
  VIMEO = 'Vimeo',
  FACEBOOK = 'Facebook',
  TWITTER = 'Twitter',
  TWITCH = 'Twitch',
  DISCORD = 'Discord',
  BILIBILI = 'bilibili',
  BILIBILI_TV = 'bilibili.tv',
  CUSTOM = 'Custom'
}

export enum EditStatus {
  PENDING = 'Pendiente',
  IN_PROGRESS = 'En Progreso',
  COMPLETED = 'Completado',
}

export enum ProcessStatus {
    PENDING = 'Pendiente',
    PROCESSING = 'Procesando',
    COMPLETED = 'Completado',
    ERROR = 'Error'
}

export enum Difficulty {
  LOW = 'Bajo',
  MEDIUM = 'Medio',
  HIGH = 'Alto',
}

export type SubscriptionType = 'playlist' | 'music' | 'hashtag' | 'saved' | 'location' | 'feed' | 'liked' | 'reels' | 'stories' | 'highlights' | 'tagged' | 'channel' | 'account' | 'watch_later' | 'favorites';

export interface Subscription {
  type: SubscriptionType;
  id: string; 
  name: string;
}

export type ListType = 'feed' | 'liked' | 'reels' | 'stories' | 'highlights' | 'tagged' | 'favorites' | 'playlist' | 'saved' | 'watch_later';

export interface List {
  type: ListType;
  name: string;
}

export interface Post {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  postUrl: string; // Renamed from videoUrl
  type: PostType;
  imageUrls?: string[]; // For image posts
  creator: string; // This is the creator's unique name/ID
  platform: Platform;
  editStatus: EditStatus;
  processStatus: ProcessStatus;
  difficulty: Difficulty;
  music?: string;
  artist?: string;
  characters?: string[];
  notes?: string;
  duration: number; // in seconds. 0 for images.
  size: number; // in MB
  downloadDate: string;
  uploadDate?: string;
  deletedAt?: string;
  subscription?: Subscription;
  lists?: List[]; // Array de listas a las que pertenece el video
}

export interface CreatorPlatformInfo {
  url: string;
  postCount: number;
  subscriptions: Subscription[];
}

export interface Creator {
    name: string; // The unique ID-like name, e.g., "MMD_Creator_X"
    displayName: string; // The display name, e.g., "MMD Creator X"
    platforms: Partial<Record<Platform, CreatorPlatformInfo>>;
}

export interface SubscriptionInfo {
    id: string;
    type: SubscriptionType;
    name: string;
    platform: Platform;
    url?: string;
    postCount: number;
    creatorCount?: number; // For special lists
    creator?: string; // For account subscriptions
}


export interface DataContextType {
  posts: Post[];
  trash: Post[];
  creators: Creator[];
  updatePost: (id: string, updates: Partial<Post>) => void;
  updateMultiplePosts: (ids: string[], updates: Partial<Post>) => void;
  moveToTrash: (id: string) => void;
  moveMultipleToTrash: (ids: string[]) => void;
  restoreFromTrash: (id: string) => void;
  deletePermanently: (id: string) => void;
  emptyTrash: () => void;
  analyzePost: (id: string) => Promise<void>;
  reanalyzePosts: (ids:string[]) => Promise<void>;
  getStats: () => {
    total: number;
    withMusic: number;
    withCharacters: number;
    processed: number;
    inTrash: number;
    pending: number;
  };
  getCreatorByName: (name: string) => Creator | undefined;
  getPostsByCreator: (creatorName: string, platform?: Platform, listId?: string) => Promise<Post[]>;
  getSubscriptionInfo: (type: SubscriptionType, id: string) => SubscriptionInfo | undefined;
  getPostsBySubscription: (type: SubscriptionType, id: string, list?: string) => Post[];
}

// Interfaz específica para paginación infinita
export interface InfiniteScrollDataContextType extends DataContextType {
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  error: string | null;
  loadMoreVideos: () => Promise<void>;
}
