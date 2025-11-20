
export enum PostType {
  VIDEO = 'Video',
  IMAGE = 'Image',
}

export enum Platform {
  YOUTUBE = 'youtube',
  TIKTOK = 'tiktok',
  INSTAGRAM = 'instagram',
  BILIBILI = 'bilibili',
  FACEBOOK = 'facebook',
  TWITTER = 'twitter',
  CUSTOM = 'custom'
}

export enum EditStatus {
  PENDING = 'pendiente',
  IN_PROGRESS = 'en_proceso',
  COMPLETED = 'completado',
  DISCARDED = 'descartado'
}

export enum ProcessStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

export enum Difficulty {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}

export type SubscriptionType = 'account' | 'playlist' | 'hashtag' | 'location' | 'music' | 'search' | 'liked' | 'saved' | 'folder' | 'watch_later';

export interface Subscription {
  type: SubscriptionType;
  id: string | number;
  name: string;
}

export type CategoryType = 'videos' | 'shorts' | 'feed' | 'reels' | 'stories' | 'highlights' | 'tagged';

export interface PostCategory {
  type: CategoryType;
  name: string;
}

export interface PostList {
  type: CategoryType;
}

export interface Post {
  id: string;
  title: string;
  thumbnailUrl: string;
  postUrl: string; // Para reproducción interna
  originalUrl?: string; // Para enlace original externo
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
  downloadDate?: string;
  publicationDate?: string;
  deletedAt?: string;
  subscription?: Subscription;
  categories?: PostCategory[]; // Array de categorías del post (videos, shorts, feed, etc.)
  lists?: PostList[]; // Array de listas/categorías de suscripción que contiene este post
  isCarousel?: boolean;
  carouselCount?: number;
}

export interface CreatorPlatformInfo {
  url: string;
  postCount: number;
  subscriptions: Subscription[];
}

export interface Creator {
  id: number;
  name: string; // The creator name
  displayName: string; // The display name
  platforms: Partial<Record<Platform, CreatorPlatformInfo>>;
  parentCreatorId?: number; // For alias relationships
  isPrimary: boolean;
  aliasType?: 'main' | 'alias' | 'variation';
}

export interface SubscriptionInfo {
  id: number;
  name: string;
  type: SubscriptionType;
  platform: Platform;
  url?: string;
  postCount: number;
  isAccount: boolean; // TRUE for account subscriptions
  creatorId?: number; // For account subscriptions
  creatorName?: string; // Creator name for display
  externalUuid?: string; // For 4K apps mapping
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
  deletePermanently: (id: string) => Promise<{ success: boolean, message?: string }>;
  emptyTrash: () => void;
  analyzePost: (id: string) => Promise<void>;
  reanalyzePosts: (ids: string[]) => Promise<void>;
  getStats: () => {
    total: number;
    totalInDB: number;
    withMusic: number;
    withCharacters: number;
    processed: number;
    inTrash: number;
    pending: number;
  };
  getCreatorByName: (name: string) => Creator | undefined;
  getPostsByCreator: (creatorName: string, platform?: Platform, listId?: string) => Promise<Post[]>;
  getSubscriptionInfo: (type: SubscriptionType, id: number) => SubscriptionInfo | undefined;
  getPostsBySubscription: (type: SubscriptionType, id: number, category?: CategoryType) => Post[];
}

// Interfaz específica para paginación infinita
export interface InfiniteScrollDataContextType extends DataContextType {
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  error: string | null;
  loadMoreVideos: () => Promise<void>;
}
