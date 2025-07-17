# 🔧 Plan de Refactorización de maintenance.py

## 📋 **Contexto Actual**

El archivo `maintenance.py` tiene **2,620 líneas** y contiene múltiples responsabilidades:

### 🎯 **Funcionalidades Actuales Utilizadas por la App Web:**
- `populate_database()` - Población completa de BD desde fuentes externas
- `regenerate_thumbnails()` - Regeneración selectiva de thumbnails

### 🔄 **Funcionalidades Adicionales (35+ métodos):**
- Backup/restore del sistema
- Limpieza de thumbnails huérfanos
- Verificación de integridad
- Optimización de BD
- Gestión de personajes
- Análisis de títulos
- Configuración de thumbnails
- Y muchas más...

## 🎯 **Objetivos de Refactorización**

### 1. **Separación de Responsabilidades**
- Dividir en módulos especializados por función
- Mantener compatibilidad CLI existente
- Facilitar uso programático desde la app web

### 2. **Mejora para Integración Web**
- Crear API programática para operaciones específicas
- Soporte para IDs específicos en operaciones
- Mejores reportes de progreso
- Manejo granular de errores

### 3. **Optimización de Estructura**
- Eliminar código duplicado
- Mejorar performance
- Documentación consistente

## 📁 **Estructura Propuesta**

```
src/
├── maintenance/
│   ├── __init__.py                 # Exporta interfaces públicas
│   ├── cli.py                      # CLI wrapper (mantiene compatibilidad)
│   ├── database_ops.py             # Operaciones de BD
│   ├── thumbnail_ops.py            # Operaciones de thumbnails
│   ├── backup_ops.py               # Backup/restore
│   ├── character_ops.py            # Gestión de personajes
│   ├── integrity_ops.py            # Verificación/limpieza
│   └── utils.py                    # Utilidades comunes
│
└── maintenance_api.py              # API programática para app web
```

## 🔧 **Módulos Específicos**

### 1. **src/maintenance/thumbnail_ops.py**
**Responsabilidades:**
- Generación de thumbnails
- Regeneración selectiva
- Limpieza de thumbnails huérfanos
- Validación de calidad

**Nuevas funcionalidades requeridas:**
```python
def regenerate_thumbnails_by_ids(video_ids: List[int], force: bool = False) -> Dict:
    """Regenerar thumbnails para IDs específicos"""
    
def get_thumbnail_stats(video_ids: List[int] = None) -> Dict:
    """Estadísticas de thumbnails por IDs o globales"""
```

### 2. **src/maintenance/database_ops.py**
**Responsabilidades:**
- Población de BD
- Optimización de BD
- Limpieza de registros
- Migración de datos

**Funcionalidades existentes a mantener:**
```python
def populate_database(source='all', platform=None, limit=None, force=False, file_path=None)
def optimize_database()
def clear_database(platform=None, force=False)
```

### 3. **src/maintenance/backup_ops.py**
**Responsabilidades:**
- Backup completo del sistema
- Restore desde backup
- Limpieza de backups antiguos

### 4. **src/maintenance/character_ops.py**
**Responsabilidades:**
- Gestión de personajes
- Análisis de títulos
- Mapeo de creadores
- Limpieza de falsos positivos

### 5. **src/maintenance/integrity_ops.py**
**Responsabilidades:**
- Verificación de integridad
- Detección de archivos faltantes
- Reparación automática
- Estadísticas del sistema

### 6. **src/maintenance_api.py** (Nueva API Web)
**Funcionalidades específicas para la app web:**
```python
class MaintenanceAPI:
    """API programática para operaciones de mantenimiento desde la app web"""
    
    def regenerate_thumbnails_bulk(self, video_ids: List[int], force: bool = False) -> Dict:
        """Regenerar thumbnails para videos específicos"""
        
    def get_operation_progress(self, operation_id: str) -> Dict:
        """Obtener progreso de operación en curso"""
        
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancelar operación en curso"""
        
    def get_system_health(self) -> Dict:
        """Estado general del sistema"""
```

## 🚀 **Implementación por Fases**

### **Fase 1: Extracción de Thumbnail Operations**
**Prioridad:** ALTA (Necesario para app web)
- Extraer todas las funciones relacionadas con thumbnails
- Implementar `regenerate_thumbnails_by_ids()`
- Mantener compatibilidad con CLI existente
- Integrar con app web

### **Fase 2: API Web Especializada**
**Prioridad:** ALTA
- Crear `src/maintenance_api.py`
- Implementar progreso de operaciones
- Integrar con endpoint Flask

### **Fase 3: Refactorización de Database Operations**
**Prioridad:** MEDIA
- Extraer operaciones de BD
- Optimizar consultas existentes
- Mejorar logging

### **Fase 4: Reorganización Completa**
**Prioridad:** MEDIA
- Dividir resto de funcionalidades
- Crear CLI wrapper
- Actualizar documentación

### **Fase 5: Mejoras Adicionales**
**Prioridad:** BAJA
- Operaciones asíncronas
- Web UI para monitoreo
- Notificaciones en tiempo real

## 📝 **Compatibilidad CLI**

### **Mantener Interfaz Existente:**
```bash
# Estos comandos deben seguir funcionando igual
python maintenance.py populate-db --source all --limit 20
python maintenance.py regenerate-thumbnails --force
python maintenance.py backup
python maintenance.py show-stats
```

### **Nueva Funcionalidad:**
```bash
# Regenerar thumbnails para IDs específicos
python maintenance.py regenerate-thumbnails --ids 1,2,3,4,5 --force
python maintenance.py regenerate-thumbnails --ids 1,2,3,4,5 --progress
```

## 🔗 **Integración con App Web**

### **Endpoint Flask actualizado:**
```python
@app.route('/api/videos/bulk-edit', methods=['POST'])
def api_bulk_edit_videos():
    # ...código existente...
    
    # Regenerar thumbnails con nueva API
    if options.get('regenerate_thumbnails'):
        from src.maintenance_api import MaintenanceAPI
        maintenance_api = MaintenanceAPI()
        
        result = maintenance_api.regenerate_thumbnails_bulk(
            video_ids=video_ids,
            force=True
        )
        
        if result['success']:
            additional_actions.append(f"thumbnails regenerados: {result['count']}")
        else:
            additional_actions.append(f"error regenerando thumbnails: {result['error']}")
```

## 💡 **Beneficios Esperados**

### **Para Desarrolladores:**
- Código más mantenible y testeable
- Separación clara de responsabilidades
- Reutilización de componentes

### **Para la App Web:**
- Operaciones granulares por IDs
- Mejor reporting de progreso
- Manejo de errores más específico
- Timeouts y cancelación

### **Para CLI:**
- Mantiene funcionalidad existente
- Nuevas opciones para operaciones específicas
- Mejor performance

## 🎯 **Primer Paso: Implementar Thumbnail Operations**

### **Tarea Inmediata:**
1. Crear `src/maintenance/thumbnail_ops.py`
2. Extraer funciones relacionadas con thumbnails
3. Implementar `regenerate_thumbnails_by_ids()`
4. Actualizar `maintenance.py` para usar nuevo módulo
5. Integrar con app web

### **Resultado Esperado:**
```python
# En app.py
if options.get('regenerate_thumbnails'):
    from src.maintenance.thumbnail_ops import regenerate_thumbnails_by_ids
    
    result = regenerate_thumbnails_by_ids(video_ids, force=True)
    if result['success']:
        additional_actions.append(f"thumbnails regenerados: {result['successful']}")
    else:
        additional_actions.append(f"error regenerando thumbnails: {result['error']}")
```

## 🎉 **Conclusión**

Esta refactorización permitirá:
- ✅ **Regenerar thumbnails** para videos específicos desde la app web
- ✅ Mantener toda la funcionalidad CLI existente
- ✅ Código más organizado y mantenible
- ✅ Base sólida para futuras mejoras

**Próximo paso:** Implementar Fase 1 con foco en thumbnail operations para habilitar la funcionalidad "Regenerar thumbnails" en la edición masiva.