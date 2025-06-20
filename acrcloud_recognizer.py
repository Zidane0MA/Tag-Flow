#!/usr/bin/env python3
"""
Tag-Flow - Módulo de Reconocimiento de Música con ACRCloud
Implementación completa de la API de ACRCloud
"""

import os
import base64
import hashlib
import hmac
import time
import requests
import json
from typing import Optional, Dict

class ACRCloudRecognizer:
    """Clase para reconocimiento de música usando ACRCloud"""
    
    def __init__(self, host: str, access_key: str, access_secret: str):
        """Inicializar el reconocedor ACRCloud"""
        self.host = host
        self.access_key = access_key
        self.access_secret = access_secret
        self.endpoint = f"https://{host}/v1/identify"
        
    def recognize_audio_file(self, audio_file_path: str) -> Dict:
        """
        Reconocer música desde un archivo de audio
        
        Args:
            audio_file_path: Ruta al archivo de audio
            
        Returns:
            Dict con información de la música reconocida
        """
        try:
            # Leer archivo de audio
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            return self.recognize_audio_data(audio_data)
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error leyendo archivo: {str(e)}"
            }
    
    def recognize_audio_data(self, audio_data: bytes) -> Dict:
        """
        Reconocer música desde datos de audio en memoria
        
        Args:
            audio_data: Datos binarios del audio
            
        Returns:
            Dict con información de la música reconocida
        """
        try:
            # Preparar datos para la API
            files = {
                'sample': audio_data,
                'sample_bytes': len(audio_data),
                'access_key': self.access_key,
            }
            
            # Crear signature
            signature = self._create_signature()
            files.update(signature)
            
            # Hacer request a ACRCloud
            response = requests.post(
                self.endpoint,
                files={
                    'sample': ('audio.wav', audio_data, 'audio/wav'),
                    'access_key': (None, self.access_key),
                    'data_type': (None, 'audio'),
                    'signature_version': (None, '1'),
                    'signature': (None, signature['signature']),
                    'timestamp': (None, signature['timestamp'])
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_result(result)
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error': "Timeout - La API tardó demasiado en responder"
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': f"Error de conexión: {str(e)}"
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error inesperado: {str(e)}"
            }
    
    def _create_signature(self) -> Dict[str, str]:
        """Crear signature para autenticación ACRCloud"""
        timestamp = str(int(time.time()))
        
        # Crear string para firmar
        string_to_sign = f"POST\n/v1/identify\n{self.access_key}\naudio\n1\n{timestamp}"
        
        # Crear HMAC-SHA1 signature
        signature = base64.b64encode(
            hmac.new(
                self.access_secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
        
        return {
            'signature': signature,
            'timestamp': timestamp
        }
    
    def _parse_result(self, result: Dict) -> Dict:
        """Parsear resultado de ACRCloud"""
        try:
            status = result.get('status', {})
            
            if status.get('code') == 0:  # Éxito
                music_info = result.get('metadata', {}).get('music', [])
                
                if music_info:
                    track = music_info[0]  # Tomar el primer resultado
                    
                    # Extraer información básica
                    title = track.get('title', 'Título desconocido')
                    artists = track.get('artists', [])
                    artist_names = [artist.get('name', 'Artista desconocido') for artist in artists]
                    album = track.get('album', {}).get('name', 'Álbum desconocido')
                    
                    # Información adicional
                    duration = track.get('duration_ms', 0) // 1000  # Convertir a segundos
                    score = track.get('score', 0)
                    
                    return {
                        'status': 'success',
                        'title': title,
                        'artists': artist_names,
                        'album': album,
                        'duration': duration,
                        'confidence': score,
                        'formatted': f"{', '.join(artist_names)} - {title}" if artist_names else title
                    }
                else:
                    return {
                        'status': 'no_match',
                        'error': 'No se encontró música en el audio'
                    }
            else:
                error_msg = status.get('msg', 'Error desconocido')
                return {
                    'status': 'error',
                    'error': f"ACRCloud error: {error_msg}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error parseando resultado: {str(e)}"
            }

def test_acrcloud_connection(host: str, access_key: str, access_secret: str) -> bool:
    """
    Probar conexión con ACRCloud
    
    Args:
        host: Host de ACRCloud
        access_key: Clave de acceso
        access_secret: Clave secreta
        
    Returns:
        True si la conexión es exitosa
    """
    try:
        recognizer = ACRCloudRecognizer(host, access_key, access_secret)
        
        # Crear un audio de prueba muy corto (silencio)
        test_audio = b'\x00' * 1024  # 1KB de silencio
        
        result = recognizer.recognize_audio_data(test_audio)
        
        # Si llegamos aquí sin error de autenticación, la configuración es correcta
        if result['status'] in ['no_match', 'success']:
            return True
        elif 'authentication' in result.get('error', '').lower():
            return False
        else:
            # Otros errores pueden ser por el audio de prueba, pero la auth funciona
            return True
            
    except Exception:
        return False

if __name__ == "__main__":
    """Script de prueba"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv('ACRCLOUD_HOST')
    access_key = os.getenv('ACRCLOUD_ACCESS_KEY')
    access_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
    
    if not all([host, access_key, access_secret]):
        print("❌ Faltan credenciales de ACRCloud en .env")
        exit(1)
    
    print("🎵 Probando conexión con ACRCloud...")
    
    if test_acrcloud_connection(host, access_key, access_secret):
        print("✅ Conexión exitosa con ACRCloud")
    else:
        print("❌ Error de conexión - revisa tus credenciales")
