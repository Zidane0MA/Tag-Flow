/**
 * 🔗 WebSocket Service - Cliente para actualizaciones en tiempo real
 * Conecta con el backend WebSocket para invalidación de cache y updates
 */

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  message_id: string;
}

interface VideoUpdateData {
  video_id: string;
  action: 'update' | 'delete' | 'restore' | 'move_to_trash';
  changes: Record<string, any>;
  timestamp: string;
}

interface CacheInvalidationData {
  cache_keys: string[];
  reason: string;
  timestamp: string;
}

type WebSocketEventHandler = (data: any) => void;

class WebSocketService {
  private websocket: WebSocket | null = null;
  private connected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000; // 1 segundo inicial
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private clientId: string | null = null;

  // Configuración
  private readonly websocketUrl = 'ws://localhost:8766';
  private readonly heartbeatInterval = 30000; // 30 segundos
  private heartbeatTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.setupEventHandlers();
  }

  /**
   * Conectar al servidor WebSocket
   */
  async connect(): Promise<boolean> {
    if (this.connected) {
      console.log('🔗 WebSocket ya está conectado');
      return true;
    }

    try {
      console.log('🔗 Conectando a WebSocket...', this.websocketUrl);

      this.websocket = new WebSocket(this.websocketUrl);

      this.websocket.onopen = this.handleOpen.bind(this);
      this.websocket.onmessage = this.handleMessage.bind(this);
      this.websocket.onclose = this.handleClose.bind(this);
      this.websocket.onerror = this.handleError.bind(this);

      // Esperar conexión (con timeout)
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          console.warn('🔗 Timeout conectando WebSocket');
          resolve(false);
        }, 5000);

        this.websocket!.onopen = (event) => {
          clearTimeout(timeout);
          this.handleOpen(event);
          resolve(true);
        };

        this.websocket!.onerror = () => {
          clearTimeout(timeout);
          resolve(false);
        };
      });

    } catch (error) {
      console.error('🔗 Error conectando WebSocket:', error);
      return false;
    }
  }

  /**
   * Desconectar del servidor
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.connected = false;
    this.stopHeartbeat();
    console.log('🔗 WebSocket desconectado');
  }

  /**
   * Verificar si está conectado
   */
  isConnected(): boolean {
    return this.connected && this.websocket?.readyState === WebSocket.OPEN;
  }

  /**
   * Registrar handler para eventos específicos
   */
  on(eventType: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  /**
   * Remover handler para eventos
   */
  off(eventType: string, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Suscribirse a una operación específica
   */
  subscribeToOperation(operationId: string): void {
    if (this.isConnected()) {
      this.send({
        action: 'subscribe',
        operation_id: operationId
      });
    }
  }

  /**
   * Desuscribirse de una operación
   */
  unsubscribeFromOperation(operationId: string): void {
    if (this.isConnected()) {
      this.send({
        action: 'unsubscribe',
        operation_id: operationId
      });
    }
  }

  /**
   * Solicitar estado del servidor
   */
  requestServerStatus(): void {
    if (this.isConnected()) {
      this.send({
        action: 'get_status'
      });
    }
  }

  // --- Handlers de eventos ---

  private handleOpen(event: Event): void {
    console.log('🔗 WebSocket conectado exitosamente');
    this.connected = true;
    this.reconnectAttempts = 0;
    this.startHeartbeat();

    // Emitir evento de conexión
    this.emit('connected', { timestamp: new Date().toISOString() });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Procesar mensaje según tipo
      switch (message.type) {
        case 'notification':
          this.handleNotification(message.data);
          break;

        case 'operation_progress':
          this.emit('operation_progress', message.data);
          break;

        case 'operation_complete':
          this.emit('operation_complete', message.data);
          break;

        case 'operation_failed':
          this.emit('operation_failed', message.data);
          break;

        case 'system_status':
          this.emit('system_status', message.data);
          break;

        case 'heartbeat':
          this.handleHeartbeat(message.data);
          break;

        default:
          console.log('🔗 Mensaje WebSocket desconocido:', message.type, message.data);
      }

    } catch (error) {
      console.error('🔗 Error procesando mensaje WebSocket:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('🔗 WebSocket cerrado:', event.code, event.reason);
    this.connected = false;
    this.stopHeartbeat();

    this.emit('disconnected', {
      code: event.code,
      reason: event.reason,
      timestamp: new Date().toISOString()
    });

    // Intentar reconexión
    this.attemptReconnect();
  }

  private handleError(event: Event): void {
    console.error('🔗 Error WebSocket:', event);
    this.emit('error', { error: event, timestamp: new Date().toISOString() });
  }

  private handleNotification(data: any): void {
    // Extraer client_id del mensaje de bienvenida
    if (data.client_id && !this.clientId) {
      this.clientId = data.client_id;
      console.log('🔗 Client ID asignado:', this.clientId);
    }

    // Procesar notificaciones especiales
    if (data.level === 'cursor_invalidation' && data.data?.type === 'video_update') {
      this.handleVideoUpdate(data.data.video_update);
    } else if (data.level === 'cache_invalidation' && data.data?.type === 'cache_invalidation') {
      this.handleCacheInvalidation(data.data.cache_invalidation);
    }

    // Emitir notificación general
    this.emit('notification', data);
  }

  private handleVideoUpdate(updateData: VideoUpdateData): void {
    console.log('🔗 Video update recibido:', updateData);
    this.emit('video_update', updateData);
  }

  private handleCacheInvalidation(invalidationData: CacheInvalidationData): void {
    console.log('🔗 Cache invalidation recibido:', invalidationData);
    this.emit('cache_invalidation', invalidationData);
  }

  private handleHeartbeat(data: any): void {
    if (data.type === 'ping') {
      // Responder con pong
      this.send({
        action: 'ping'
      });
    }
    // Emitir heartbeat para stats
    this.emit('heartbeat', data);
  }

  // --- Utilidades ---

  private send(data: any): void {
    if (this.isConnected()) {
      this.websocket!.send(JSON.stringify(data));
    } else {
      console.warn('🔗 Intentando enviar mensaje sin conexión WebSocket');
    }
  }

  private emit(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`🔗 Error en handler ${eventType}:`, error);
        }
      });
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('🔗 Máximo número de reconexiones alcanzado. WebSocket en modo fallback.');
      this.emit('max_reconnects_reached', { attempts: this.reconnectAttempts });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000); // Max 30s

    console.log(`🔗 Reintentando conexión en ${delay}ms (intento ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().then(success => {
        if (!success) {
          this.attemptReconnect();
        }
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.requestServerStatus();
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private setupEventHandlers(): void {
    // Setup para auto-reconexión en visibilidad
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && !this.isConnected()) {
        console.log('🔗 Página visible, intentando reconectar WebSocket');
        this.connect();
      }
    });

    // Cleanup al cerrar página
    window.addEventListener('beforeunload', () => {
      this.disconnect();
    });
  }

  /**
   * Obtener estadísticas de conexión
   */
  getConnectionStats() {
    return {
      connected: this.connected,
      clientId: this.clientId,
      reconnectAttempts: this.reconnectAttempts,
      websocketUrl: this.websocketUrl,
      readyState: this.websocket?.readyState || WebSocket.CLOSED
    };
  }
}

// Instancia singleton
export const websocketService = new WebSocketService();

// Auto-connect cuando se carga el módulo (con delay para dar tiempo al backend)
setTimeout(() => {
  websocketService.connect().catch(error => {
    console.warn('🔗 Auto-connect WebSocket falló. Continuando sin WebSocket:', error);
  });
}, 2000); // 2 segundos de delay

export default websocketService;