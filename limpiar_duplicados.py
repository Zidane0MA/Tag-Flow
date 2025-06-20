#!/usr/bin/env python3
"""
Tag-Flow - Limpiador de Duplicados
Utilidad para limpiar duplicados del CSV de videos
"""

import pandas as pd
from pathlib import Path

def clean_duplicates():
    """Limpiar duplicados del CSV de videos"""
    csv_path = Path("data/videos.csv")
    
    if not csv_path.exists():
        print("❌ No se encontró el archivo data/videos.csv")
        return False
    
    try:
        # Cargar datos
        df = pd.read_csv(csv_path)
        initial_count = len(df)
        
        print(f"📊 Videos en el CSV: {initial_count}")
        
        # Verificar duplicados
        duplicates = df['ruta_absoluta'].duplicated()
        duplicate_count = duplicates.sum()
        
        if duplicate_count == 0:
            print("✅ No hay duplicados en el CSV")
            return True
        
        print(f"⚠️ Encontrados {duplicate_count} duplicados")
        
        # Mostrar duplicados
        print("\n🔍 Videos duplicados:")
        duplicate_files = df[duplicates]['archivo'].tolist()
        for i, file in enumerate(duplicate_files, 1):
            print(f"  {i}. {file}")
        
        # Limpiar duplicados (mantener el último)
        df_clean = df.drop_duplicates(subset=['ruta_absoluta'], keep='last')
        final_count = len(df_clean)
        
        # Crear backup
        backup_path = csv_path.with_suffix('.backup.csv')
        df.to_csv(backup_path, index=False)
        print(f"💾 Backup creado: {backup_path}")
        
        # Guardar CSV limpio
        df_clean.to_csv(csv_path, index=False)
        
        print(f"🧹 CSV limpiado:")
        print(f"  - Videos antes: {initial_count}")
        print(f"  - Videos después: {final_count}")
        print(f"  - Duplicados eliminados: {initial_count - final_count}")
        print(f"✅ CSV actualizado: {csv_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando duplicados: {e}")
        return False

def main():
    """Función principal"""
    print("🧹 Tag-Flow - Limpiador de Duplicados")
    print("=" * 40)
    
    if clean_duplicates():
        print("\n🎉 ¡Limpieza completada!")
    else:
        print("\n❌ Error durante la limpieza")

if __name__ == "__main__":
    main()
