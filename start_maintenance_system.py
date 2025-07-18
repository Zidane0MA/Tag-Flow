#!/usr/bin/env python3
"""
🚀 Start Maintenance System
Script de inicialización para el sistema de mantenimiento enterprise
"""

import os
import sys
import time
import logging
import threading
import asyncio
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    🚀 Inicializar sistema de mantenimiento enterprise
    """
    print("🔧 Tag-Flow V2 - Enterprise Maintenance System")
    print("=" * 50)
    
    try:
        # 1. Inicializar WebSocket Manager
        logger.info("🔗 Inicializando WebSocket Manager...")
        from src.maintenance.websocket_manager import get_websocket_manager
        
        def start_websocket_server():
            """Iniciar servidor WebSocket en thread separado"""
            try:
                manager = get_websocket_manager()
                asyncio.run(manager.start_server())
            except Exception as e:
                logger.error(f"Error iniciando servidor WebSocket: {e}")
        
        ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
        ws_thread.start()
        logger.info("✅ WebSocket Manager iniciado")
        
        # 2. Inicializar Operation Manager
        logger.info("⚙️ Inicializando Operation Manager...")
        from src.maintenance.operation_manager import get_operation_manager
        
        operation_manager = get_operation_manager()
        logger.info("✅ Operation Manager iniciado")
        
        # 3. Inicializar Maintenance API
        logger.info("🔧 Inicializando Maintenance API...")
        from src.maintenance_api import get_maintenance_api
        
        api = get_maintenance_api()
        logger.info("✅ Maintenance API iniciada")
        
        # 4. Configurar Flask (opcional)
        configure_flask = input("¿Configurar endpoints Flask? (y/N): ").lower() == 'y'
        
        if configure_flask:
            logger.info("🌐 Configurando Flask endpoints...")
            from src.maintenance.flask_endpoints import register_maintenance_routes
            
            try:
                from flask import Flask
                
                app = Flask(__name__)
                app.secret_key = 'maintenance_system_secret_key'
                
                # Registrar rutas
                register_maintenance_routes(app)
                
                # Iniciar Flask en thread separado
                def run_flask():
                    app.run(host='0.0.0.0', port=5001, debug=False)
                
                flask_thread = threading.Thread(target=run_flask, daemon=True)
                flask_thread.start()
                
                logger.info("✅ Flask endpoints configurados en puerto 5001")
                
            except ImportError:
                logger.warning("Flask no disponible, saltando configuración web")
        
        # 5. Mostrar información del sistema
        time.sleep(2)  # Esperar a que se inicialicen los servicios
        
        print("\n🎯 Sistema de mantenimiento iniciado exitosamente!")
        print("=" * 50)
        
        # Mostrar estadísticas
        try:
            stats = api.get_api_stats()
            print(f"📊 API Version: {stats['api_version']}")
            print(f"🔧 Features: {', '.join(stats['features'])}")
            
            health = api.get_system_health()
            print(f"💚 System Health: {health.get('health_score', 'N/A')}/100")
            
        except Exception as e:
            logger.warning(f"Error obteniendo estadísticas: {e}")
        
        # URLs de acceso
        print("\n🌐 URLs de acceso:")
        print("  • WebSocket Server: ws://localhost:8765")
        if configure_flask:
            print("  • Dashboard: http://localhost:5001/maintenance/dashboard")
            print("  • API: http://localhost:5001/maintenance/api/")
            print("  • WebSocket Test: http://localhost:5001/maintenance/test/websocket")
        
        # 6. Crear operación de prueba
        create_test = input("\n¿Crear operación de prueba? (y/N): ").lower() == 'y'
        
        if create_test:
            logger.info("🧪 Creando operación de prueba...")
            
            def test_operation(progress_callback=None):
                """Operación de prueba"""
                total = 10
                for i in range(total):
                    if progress_callback:
                        progress_callback(
                            processed=i + 1,
                            total=total,
                            current_item=f"Procesando item {i + 1}",
                            successful=i + 1,
                            failed=0
                        )
                    time.sleep(1)
                return {'message': 'Operación de prueba completada', 'items_processed': total}
            
            operation_id = operation_manager.create_operation(
                "test_operation",
                total_items=10,
                notification_interval=0.5
            )
            
            success = operation_manager.start_operation(operation_id, test_operation)
            
            if success:
                print(f"✅ Operación de prueba iniciada: {operation_id}")
                
                # Monitorear progreso
                print("\n📊 Monitoreando progreso...")
                while True:
                    status = operation_manager.get_operation_status(operation_id)
                    if status:
                        print(f"  {status['progress_percentage']:.1f}% - {status['current_step']}")
                        if not status['status'] in ['pending', 'running']:
                            break
                    time.sleep(1)
                
                print(f"✅ Operación {status['status']}")
            else:
                print("❌ No se pudo iniciar la operación de prueba")
        
        # 7. Mantener el sistema corriendo
        print("\n🔄 Sistema funcionando...")
        print("Presiona Ctrl+C para detener")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema...")
            
            # Cleanup
            operation_manager.shutdown()
            
            # Detener WebSocket server
            try:
                asyncio.run(get_websocket_manager().stop_server())
            except:
                pass
            
            print("✅ Sistema detenido")
            
    except Exception as e:
        logger.error(f"Error iniciando sistema: {e}")
        sys.exit(1)


def show_help():
    """Mostrar ayuda"""
    print("""
🔧 Tag-Flow V2 - Enterprise Maintenance System
==============================================

Características del sistema:
✅ Operaciones asíncronas con tracking de progreso
✅ WebSockets para comunicación en tiempo real
✅ Dashboard web con monitoreo en vivo
✅ Sistema de notificaciones push
✅ Cancelación y pausa de operaciones
✅ Métricas de rendimiento en tiempo real
✅ Priorización de operaciones
✅ API REST completa

Componentes:
• WebSocket Manager: Comunicación en tiempo real
• Operation Manager: Gestión de operaciones largas
• Maintenance API: API programática avanzada
• Flask Endpoints: Endpoints web para dashboard
• Dashboard HTML/JS: Interfaz de usuario

Uso:
  python start_maintenance_system.py

URLs:
  • WebSocket: ws://localhost:8765
  • Dashboard: http://localhost:5001/maintenance/dashboard
  • API: http://localhost:5001/maintenance/api/

Ejemplos de uso programático:
  from src.maintenance_api import get_maintenance_api
  api = get_maintenance_api()
  
  # Regenerar thumbnails
  operation_id = api.regenerate_thumbnails_bulk([1, 2, 3])
  
  # Monitorear progreso
  progress = api.get_operation_progress(operation_id)
  
  # Cancelar operación
  api.cancel_operation(operation_id)
""")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_help()
    else:
        main()