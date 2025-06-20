#!/usr/bin/env python3
"""
Tag-Flow - Prueba de ACRCloud
Script para probar la configuración de ACRCloud
"""

import os
from dotenv import load_dotenv
from pathlib import Path

def test_acrcloud_setup():
    """Probar configuración de ACRCloud"""
    print("🎵 Tag-Flow - Prueba de ACRCloud")
    print("=" * 40)
    
    # Cargar configuración
    load_dotenv()
    
    host = os.getenv('ACRCLOUD_HOST')
    access_key = os.getenv('ACRCLOUD_ACCESS_KEY')
    access_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
    
    print("🔍 Verificando configuración...")
    
    # Verificar que existan las variables
    if not host:
        print("❌ ACRCLOUD_HOST no configurado")
        return False
        
    if not access_key:
        print("❌ ACRCLOUD_ACCESS_KEY no configurado")
        return False
        
    if not access_secret:
        print("❌ ACRCLOUD_ACCESS_SECRET no configurado")
        return False
    
    # Verificar que no sean valores por defecto
    if access_key == "tu_access_key_aqui":
        print("❌ ACRCLOUD_ACCESS_KEY tiene valor por defecto")
        return False
        
    if access_secret == "tu_access_secret_aqui":
        print("❌ ACRCLOUD_ACCESS_SECRET tiene valor por defecto")
        return False
    
    print(f"✅ Host: {host}")
    print(f"✅ Access Key: {access_key[:8]}...{access_key[-4:]}")
    print(f"✅ Access Secret: {access_secret[:8]}...{access_secret[-4:]}")
    
    # Probar importación del módulo
    try:
        from acrcloud_recognizer import test_acrcloud_connection
        print("✅ Módulo ACRCloud importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando módulo ACRCloud: {e}")
        return False
    
    # Probar conexión
    print("\n🔌 Probando conexión con ACRCloud...")
    
    try:
        if test_acrcloud_connection(host, access_key, access_secret):
            print("✅ ¡Conexión exitosa con ACRCloud!")
            print("🎉 Tu configuración está correcta")
            return True
        else:
            print("❌ Error de conexión con ACRCloud")
            print("💡 Verifica tus credenciales en ACRCloud Console")
            return False
    except Exception as e:
        print(f"❌ Error probando conexión: {e}")
        return False

def show_configuration_help():
    """Mostrar ayuda de configuración"""
    print("\n" + "=" * 50)
    print("🛠️ CÓMO CONFIGURAR ACRCLOUD")
    print("=" * 50)
    
    print("""
1. Ve a https://console.acrcloud.com/
2. Haz clic en "Create Application"
3. Selecciona "Audio & Video Recognition" 
4. Configura:
   - Application Name: Tag-Flow-Music
   - Application Type: Audio & Video Recognition
   - Audio Type: Music
   
5. Después de crear, obtendrás:
   - Host (ej: identify-eu-west-1.acrcloud.com)
   - Access Key 
   - Access Secret
   
6. Edita tu archivo .env:
   ACRCLOUD_HOST="tu_host_aqui"
   ACRCLOUD_ACCESS_KEY="tu_access_key_aqui"
   ACRCLOUD_ACCESS_SECRET="tu_access_secret_aqui"
   
7. Ejecuta este script otra vez para probar
""")

def main():
    """Función principal"""
    
    if test_acrcloud_setup():
        print("\n🚀 ¡Listo para usar el reconocimiento de música!")
        print("   Ejecuta: python 1_script_analisis_con_musica.py")
    else:
        show_configuration_help()

if __name__ == "__main__":
    main()
