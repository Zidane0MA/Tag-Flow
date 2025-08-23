"""
Tag-Flow V2 - Missing Files Operations
Detección y limpieza de archivos faltantes en bases de datos externas
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MissingFileRecord:
    """Registro de archivo faltante"""
    db_id: str
    platform: str
    tiktok_id: str
    author: str
    description: str
    relative_path: str
    media_type: int
    expected_path: Path
    db_path: Path


class MissingFilesOperations:
    """Operaciones para detectar y limpiar archivos faltantes en BDs externas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_missing_files(self, platform: str = 'all') -> Dict[str, List[MissingFileRecord]]:
        """Detectar archivos faltantes en las BDs externas
        
        Args:
            platform: 'youtube', 'tiktok', 'instagram', 'all'
            
        Returns:
            Dict con platform -> lista de registros faltantes
        """
        results = {}
        
        if platform in ['tiktok', 'all']:
            results['tiktok'] = self._detect_missing_tiktok()
            
        if platform in ['youtube', 'all']:
            results['youtube'] = self._detect_missing_youtube()
            
        if platform in ['instagram', 'all']:
            results['instagram'] = self._detect_missing_instagram()
            
        return results
    
    def _detect_missing_tiktok(self) -> List[MissingFileRecord]:
        """Detectar archivos faltantes en 4K Tokkit"""
        missing_records = []
        
        # Rutas de 4K Tokkit
        tokkit_db_path = Path('D:/4K Tokkit/data.sqlite')
        tokkit_base_path = Path('D:/4K Tokkit')
        
        if not tokkit_db_path.exists():
            self.logger.warning(f"BD de 4K Tokkit no encontrada: {tokkit_db_path}")
            return missing_records
            
        try:
            conn = sqlite3.connect(tokkit_db_path)
            cursor = conn.cursor()
            
            # Obtener registros descargados con MediaType válido
            cursor.execute('''
                SELECT databaseId, id, authorName, description, relativePath, MediaType
                FROM MediaItems 
                WHERE downloaded = 1 
                AND relativePath IS NOT NULL 
                AND MediaType IN (2, 3)
                ORDER BY databaseId
            ''')
            
            records = cursor.fetchall()
            self.logger.info(f"Verificando {len(records)} registros de TikTok...")
            
            for record in records:
                db_id, tiktok_id, author, description, rel_path, media_type = record
                
                # Construir ruta esperada del archivo
                rel_path_clean = rel_path.lstrip('/\\')
                expected_path = tokkit_base_path / rel_path_clean
                
                # Verificar si el archivo existe
                if not expected_path.exists():
                    missing_record = MissingFileRecord(
                        db_id=db_id,  # Mantener como blob binario para UPDATE
                        platform='tiktok',
                        tiktok_id=str(tiktok_id),
                        author=author or 'Unknown',
                        description=description or '',
                        relative_path=rel_path,
                        media_type=media_type,
                        expected_path=expected_path,
                        db_path=tokkit_db_path
                    )
                    missing_records.append(missing_record)
            
            conn.close()
            self.logger.info(f"Encontrados {len(missing_records)} archivos faltantes en TikTok")
            
        except Exception as e:
            self.logger.error(f"Error detectando archivos faltantes en TikTok: {e}")
            
        return missing_records
    
    def _detect_missing_youtube(self) -> List[MissingFileRecord]:
        """Detectar archivos faltantes en 4K Video Downloader"""
        # TODO: Implementar detección para YouTube cuando sea necesario
        self.logger.info("Detección de archivos faltantes en YouTube - No implementado aún")
        return []
    
    def _detect_missing_instagram(self) -> List[MissingFileRecord]:
        """Detectar archivos faltantes en 4K Stogram"""
        # TODO: Implementar detección para Instagram cuando sea necesario
        self.logger.info("Detección de archivos faltantes en Instagram - No implementado aún")
        return []
    
    def cleanup_missing_records(self, missing_records: List[MissingFileRecord], dry_run: bool = True) -> Dict[str, int]:
        """Limpiar registros de archivos faltantes de las BDs externas
        
        Args:
            missing_records: Lista de registros a limpiar
            dry_run: Si True, solo simula la limpieza
            
        Returns:
            Dict con estadísticas de la limpieza
        """
        stats = {'cleaned': 0, 'errors': 0, 'skipped': 0}
        
        if dry_run:
            self.logger.info("🧪 MODO DRY-RUN: Simulando limpieza...")
        else:
            self.logger.info("🗑️  LIMPIANDO registros de archivos faltantes...")
        
        # Agrupar por base de datos para optimizar
        records_by_db = {}
        for record in missing_records:
            db_key = str(record.db_path)
            if db_key not in records_by_db:
                records_by_db[db_key] = []
            records_by_db[db_key].append(record)
        
        for db_path, records in records_by_db.items():
            try:
                if dry_run:
                    # En dry-run, solo contar
                    stats['cleaned'] += len(records)
                    self.logger.info(f"  📝 {len(records)} registros serían eliminados de {Path(db_path).name}")
                else:
                    # Limpieza real
                    cleaned_count = self._cleanup_records_in_db(db_path, records)
                    stats['cleaned'] += cleaned_count
                    self.logger.info(f"  ✅ {cleaned_count} registros eliminados de {Path(db_path).name}")
                    
            except Exception as e:
                self.logger.error(f"Error limpiando {db_path}: {e}")
                stats['errors'] += len(records)
        
        return stats
    
    def _cleanup_records_in_db(self, db_path: str, records: List[MissingFileRecord]) -> int:
        """Limpiar registros específicos de una base de datos"""
        cleaned_count = 0
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for record in records:
                if record.platform == 'tiktok':
                    # Para TikTok, marcar como no descargado en lugar de eliminar
                    cursor.execute('''
                        UPDATE MediaItems 
                        SET downloaded = 0
                        WHERE databaseId = ?
                    ''', (record.db_id,))
                    
                    if cursor.rowcount > 0:
                        cleaned_count += 1
                        self.logger.debug(f"Marcado como no descargado: {record.author} - {record.tiktok_id}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error ejecutando limpieza en BD: {e}")
            raise
        
        return cleaned_count
    
    def generate_missing_files_report(self, missing_records: Dict[str, List[MissingFileRecord]]) -> str:
        """Generar reporte detallado de archivos faltantes"""
        report_lines = []
        report_lines.append("🔍 REPORTE DE ARCHIVOS FALTANTES")
        report_lines.append("=" * 60)
        
        total_missing = sum(len(records) for records in missing_records.values())
        report_lines.append(f"Total archivos faltantes: {total_missing}")
        report_lines.append("")
        
        for platform, records in missing_records.items():
            if not records:
                continue
                
            report_lines.append(f"📱 {platform.upper()}: {len(records)} archivos faltantes")
            report_lines.append("-" * 40)
            
            for i, record in enumerate(records, 1):
                report_lines.append(f"")
                report_lines.append(f"🎬 ARCHIVO {i}:")
                report_lines.append(f"   Autor: {record.author}")
                
                if platform == 'tiktok':
                    report_lines.append(f"   ID: {record.tiktok_id}")
                    video_url = f"https://www.tiktok.com/@{record.author}/video/{record.tiktok_id}"
                    profile_url = f"https://www.tiktok.com/@{record.author}"
                    report_lines.append(f"   📱 Video: {video_url}")
                    report_lines.append(f"   👤 Perfil: {profile_url}")
                
                # Descripción (truncada si es muy larga)
                desc = record.description[:80] + "..." if len(record.description) > 80 else record.description
                report_lines.append(f"   Descripción: {desc}")
                
                # Información del archivo
                report_lines.append(f"   Archivo esperado: {record.expected_path.name}")
                report_lines.append(f"   Ruta: {record.relative_path}")
                report_lines.append(f"   Tipo: {'Video' if record.media_type == 2 else 'Imagen' if record.media_type == 3 else 'Otro'}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)