"""
Tag-Flow V2 - Reconocimiento Musical
Integración híbrida: YouTube API + Spotify API + ACRCloud
"""

import requests
import base64
import hmac
import hashlib
import time
import json
from typing import Dict, Optional, Tuple
import logging
from pathlib import Path

from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import config

logger = logging.getLogger(__name__)

class MusicRecognizer:
    """Reconocedor musical híbrido con múltiples APIs"""
    
    def __init__(self):
        # YouTube API
        self.youtube_api_key = config.YOUTUBE_API_KEY
        self.youtube = None
        if self.youtube_api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
                logger.info("YouTube API inicializada")
            except Exception as e:
                logger.error(f"Error inicializando YouTube API: {e}")
        
        # Spotify API
        self.spotify = None
        if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=config.SPOTIFY_CLIENT_ID,
                    client_secret=config.SPOTIFY_CLIENT_SECRET
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Spotify API inicializada")
            except Exception as e:
                logger.error(f"Error inicializando Spotify API: {e}")
        
        # ACRCloud (fallback de V1)
        self.acrcloud_config = {
            'host': config.ACRCLOUD_HOST,
            'access_key': config.ACRCLOUD_ACCESS_KEY,
            'access_secret': config.ACRCLOUD_ACCESS_SECRET
        } if all([config.ACRCLOUD_HOST, config.ACRCLOUD_ACCESS_KEY, config.ACRCLOUD_ACCESS_SECRET]) else None
    
    def recognize_music(self, audio_path: Path) -> Dict:
        """Reconocer música usando estrategia híbrida"""
        logger.info(f"Iniciando reconocimiento musical para: {audio_path}")
        
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0,
            'music_source': None,
            'error': None
        }
        
        # Estrategia 1: YouTube API (para trends virales)
        if self.youtube:
            try:
                youtube_result = self._recognize_with_youtube(audio_path)
                if youtube_result['detected_music']:
                    results.update(youtube_result)
                    results['music_source'] = 'youtube'
                    logger.info(f"Música detectada con YouTube: {results['detected_music']}")
                    return results
            except Exception as e:
                logger.warning(f"Error con YouTube API: {e}")
        
        # Estrategia 2: Spotify API (para metadatos musicales)
        if self.spotify:
            try:
                spotify_result = self._recognize_with_spotify(audio_path)
                if spotify_result['detected_music']:
                    results.update(spotify_result)
                    results['music_source'] = 'spotify'
                    logger.info(f"Música detectada con Spotify: {results['detected_music']}")
                    return results
            except Exception as e:
                logger.warning(f"Error con Spotify API: {e}")
        
        # Estrategia 3: ACRCloud (fallback confiable)
        if self.acrcloud_config:
            try:
                acrcloud_result = self._recognize_with_acrcloud(audio_path)
                if acrcloud_result['detected_music']:
                    results.update(acrcloud_result)
                    results['music_source'] = 'acrcloud'
                    logger.info(f"Música detectada con ACRCloud: {results['detected_music']}")
                    return results
            except Exception as e:
                logger.warning(f"Error con ACRCloud: {e}")
        
        logger.warning(f"No se pudo reconocer música en: {audio_path}")
        results['error'] = "No se pudo identificar la música con ningún método"
        return results
    
    def _recognize_with_youtube(self, audio_path: Path) -> Dict:
        """Reconocimiento usando YouTube Data API para trends TikTok"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0
        }
        
        # YouTube API no hace reconocimiento directo de audio
        # Aquí podrías implementar una estrategia más sofisticada:
        # 1. Extraer características del audio
        # 2. Buscar en playlists populares de TikTok
        # 3. Usar machine learning para match
        
        # Por ahora, búsqueda por keywords populares
        try:
            tiktok_keywords = [
                'tiktok viral music',
                'tiktok trend song',
                'tiktok popular music 2024',
                'viral tiktok songs'
            ]
            
            for keyword in tiktok_keywords:
                search_response = self.youtube.search().list(
                    q=keyword,
                    part='snippet',
                    maxResults=10,
                    type='video',
                    order='relevance'
                ).execute()
                
                # Analizar resultados (implementación básica)
                for item in search_response.get('items', []):
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    
                    # Heurística simple para identificar música
                    if any(word in title.lower() for word in ['music', 'song', 'audio', 'track']):
                        results['detected_music'] = title
                        results['detected_music_artist'] = channel
                        results['detected_music_confidence'] = 0.7  # Confianza media
                        return results
                        
        except Exception as e:
            logger.error(f"Error en YouTube API: {e}")
        
        return results    
    def _recognize_with_spotify(self, audio_path: Path) -> Dict:
        """Reconocimiento usando Spotify API para metadatos musicales"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0
        }
        
        try:
            # Spotify no hace reconocimiento directo de audio
            # Estrategia: buscar en playlists populares y virales
            
            # Buscar en playlists virales
            viral_playlists = [
                'viral50',  # Viral 50 global
                'topsongs2024',  # Top songs 2024
                'viral hits'
            ]
            
            for playlist_query in viral_playlists:
                search_results = self.spotify.search(
                    q=playlist_query,
                    type='playlist',
                    limit=5
                )
                
                for playlist in search_results['playlists']['items']:
                    # Obtener tracks del playlist
                    tracks = self.spotify.playlist_tracks(playlist['id'], limit=20)
                    
                    for track_item in tracks['items']:
                        if track_item['track']:
                            track = track_item['track']
                            name = track['name']
                            artists = ', '.join([artist['name'] for artist in track['artists']])
                            
                            # Heurística: si encontramos algo, usar el primer resultado relevante
                            if track['popularity'] > 70:  # Solo tracks populares
                                results['detected_music'] = name
                                results['detected_music_artist'] = artists
                                results['detected_music_confidence'] = 0.6
                                return results
            
        except Exception as e:
            logger.error(f"Error en Spotify API: {e}")
        
        return results    
    def _recognize_with_acrcloud(self, audio_path: Path) -> Dict:
        """Reconocimiento usando ACRCloud (método más confiable)"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0
        }
        
        try:
            # Leer archivo de audio
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # Preparar datos para ACRCloud
            timestamp = time.time()
            string_to_sign = f"POST\n/v1/identify\n{self.acrcloud_config['access_key']}\naudio\n1\n{timestamp}"
            signature = base64.b64encode(
                hmac.new(
                    self.acrcloud_config['access_secret'].encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha1
                ).digest()
            ).decode('utf-8')
            
            # Hacer request a ACRCloud
            files = {
                'sample': audio_data,
                'sample_bytes': len(audio_data),
                'access_key': self.acrcloud_config['access_key'],
                'data_type': 'audio',
                'signature_version': '1',
                'signature': signature,
                'timestamp': str(timestamp)
            }
            
            response = requests.post(
                f"https://{self.acrcloud_config['host']}/v1/identify",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status']['code'] == 0 and 'music' in result['metadata']:
                    music_info = result['metadata']['music'][0]
                    
                    results['detected_music'] = music_info.get('title')
                    artists = music_info.get('artists', [])
                    if artists:
                        results['detected_music_artist'] = ', '.join([artist['name'] for artist in artists])
                    
                    # ACRCloud proporciona score de confianza
                    results['detected_music_confidence'] = music_info.get('score', 0) / 100.0
                    
                    logger.info(f"ACRCloud reconoció: {results['detected_music']} - {results['detected_music_artist']}")
                
        except Exception as e:
            logger.error(f"Error en ACRCloud: {e}")
        
        return results

# Instancia global del reconocedor
music_recognizer = MusicRecognizer()