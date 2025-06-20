#!/usr/bin/env python3
"""
Tag-Flow - ACRCloud Reconocedor Oficial
Basado en el código oficial de ACRCloud
"""

import base64
import hashlib
import hmac
import os
import time
import requests
from typing import Dict

class ACRCloudRecognizer:
    """Reconocedor ACRCloud usando el código oficial"""
    
    def __init__(self, host: str, access_key: str, access_secret: str):
        self.host = host
        self.access_key = access_key
        self.access_secret = access_secret
        self.requrl = f"https://{host}/v1/identify"
        
    def recognize_audio_file(self, audio_file_path: str) -> Dict:
        """Reconocer música desde archivo usando código oficial ACRCloud"""
        try:
            # Verificar que el archivo existe
            if not os.path.exists(audio_file_path):
                return {
                    'status': 'error',
                    'error': f"Archivo no encontrado: {audio_file_path}"
                }
            
            # Parámetros según código oficial ACRCloud
            http_method = "POST"
            http_uri = "/v1/identify"
            data_type = "audio"
            signature_version = "1"
            timestamp = time.time()
            
            # Crear string para firmar (EXACTAMENTE como en código oficial)
            string_to_sign = http_method + "\n" + http_uri + "\n" + self.access_key + "\n" + data_type + "\n" + signature_version + "\n" + str(timestamp)
            
            # Crear signature (EXACTAMENTE como en código oficial)
            sign = base64.b64encode(
                hmac.new(
                    self.access_secret.encode('ascii'), 
                    string_to_sign.encode('ascii'),
                    digestmod=hashlib.sha1
                ).digest()
            ).decode('ascii')
            
            # Obtener tamaño del archivo
            sample_bytes = os.path.getsize(audio_file_path)
            
            # Preparar files (EXACTAMENTE como en código oficial)
            files = [
                ('sample', ('audio.wav', open(audio_file_path, 'rb'), 'audio/wav'))
            ]
            
            # Preparar data (EXACTAMENTE como en código oficial)
            data = {
                'access_key': self.access_key,
                'sample_bytes': sample_bytes,
                'timestamp': str(timestamp),
                'signature': sign,
                'data_type': data_type,
                'signature_version': signature_version
            }
            
            # Hacer petición (EXACTAMENTE como en código oficial)
            response = requests.post(self.requrl, files=files, data=data, timeout=30)
            response.encoding = "utf-8"
            
            # Cerrar archivo
            files[0][1][1].close()
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return self._parse_result(result)
                except Exception as e:
                    return {
                        'status': 'error',
                        'error': f"Error parseando respuesta JSON: {e}"
                    }
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error: {str(e)}"
            }
    
    def recognize_audio_data(self, audio_data: bytes) -> Dict:
        """Reconocer música desde datos en memoria"""
        # Crear archivo temporal
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Usar el método de archivo
            result = self.recognize_audio_file(temp_path)
            
            # Limpiar archivo temporal
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error con archivo temporal: {str(e)}"
            }
    
    def _parse_result(self, result: Dict) -> Dict:
        """Parsear resultado de ACRCloud"""
        try:
            status = result.get('status', {})
            
            if status.get('code') == 0:  # Éxito
                music_info = result.get('metadata', {}).get('music', [])
                
                if music_info:
                    track = music_info[0]
                    
                    title = track.get('title', 'Título desconocido')
                    artists = track.get('artists', [])
                    artist_names = [artist.get('name', 'Artista desconocido') for artist in artists]
                    album = track.get('album', {}).get('name', 'Álbum desconocido')
                    
                    return {
                        'status': 'success',
                        'title': title,
                        'artists': artist_names,
                        'album': album,
                        'confidence': track.get('score', 0),
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
                    'error': f"ACRCloud: {error_msg}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error parseando resultado: {str(e)}"
            }

def test_acrcloud_connection(host: str, access_key: str, access_secret: str) -> bool:
    """Probar conexión con ACRCloud"""
    try:
        recognizer = ACRCloudRecognizer(host, access_key, access_secret)
        
        # Crear archivo de audio de prueba muy pequeño
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Escribir header WAV mínimo + un poco de silencio
            wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            silence = b'\x00' * 1000
            temp_file.write(wav_header + silence)
            temp_path = temp_file.name
        
        try:
            result = recognizer.recognize_audio_file(temp_path)
            
            # Limpiar
            os.unlink(temp_path)
            
            # Si no hay error de autenticación, las credenciales funcionan
            if result['status'] in ['no_match', 'success']:
                return True
            elif 'authentication' in result.get('error', '').lower() or 'invalid' in result.get('error', '').lower():
                return False
            else:
                return True
                
        except Exception:
            try:
                os.unlink(temp_path)
            except:
                pass
            return False
            
    except Exception:
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv('ACRCLOUD_HOST')
    access_key = os.getenv('ACRCLOUD_ACCESS_KEY')
    access_secret = os.getenv('ACRCLOUD_ACCESS_SECRET')
    
    if not all([host, access_key, access_secret]):
        print("❌ Faltan credenciales de ACRCloud en .env")
    else:
        print("🎵 Probando ACRCloud con código oficial...")
        if test_acrcloud_connection(host, access_key, access_secret):
            print("✅ Conexión exitosa con código oficial")
        else:
            print("❌ Error de conexión - revisa credenciales")
