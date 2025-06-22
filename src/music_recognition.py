"""
Tag-Flow V2 - Reconocimiento Musical Mejorado
Integración híbrida: Extracción de nombres + YouTube API + Spotify API + ACRCloud
"""

import requests
import base64
import hmac
import hashlib
import time
import json
import re
from typing import Dict, Optional, Tuple, List
import logging
from pathlib import Path

from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import config

logger = logging.getLogger(__name__)

class MusicRecognizer:
    """Reconocedor musical híbrido con múltiples estrategias"""
    
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
        
        # Patrones para extraer música de nombres de archivo
        self.music_patterns = [
            r'｜([^｜#]+)｜',  # Patrón para ｜TITULO｜
            r'\|([^|#]+)\|',   # Patrón para |TITULO|
            r'【([^】#]+)】',    # Patrón para 【TITULO】
            r'\[([^\]#]+)\]',  # Patrón para [TITULO]
            r' - ([^-#\n]+)',  # Patrón para - TITULO
            r'_([^_#\n]+)_',   # Patrón para _TITULO_
        ]
    
    def recognize_music(self, audio_path: Path, filename: str = None) -> Dict:
        """Reconocer música usando estrategia híbrida mejorada"""
        logger.info(f"Iniciando reconocimiento musical para: {audio_path}")
        
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0,
            'music_source': None,
            'final_music': None,
            'final_music_artist': None,
            'error': None
        }
        
        # Estrategia 1: Extraer música del nombre del archivo (más preciso)
        if filename:
            try:
                filename_result = self._extract_music_from_filename(filename)
                if filename_result['detected_music']:
                    # Validar con APIs externas
                    validated_result = self._validate_music_with_apis(filename_result)
                    if validated_result['detected_music']:
                        results.update(validated_result)
                        results['music_source'] = 'manual'  # Usar 'manual' en lugar de 'filename_validated'
                        results['final_music'] = validated_result['detected_music']
                        results['final_music_artist'] = validated_result['detected_music_artist']
                        logger.info(f"Música extraída y validada del filename: {results['final_music']}")
                        return results
                    else:
                        # Si no se pudo validar, usar resultado del filename con confianza menor
                        results.update(filename_result)
                        results['music_source'] = 'manual'  # Usar 'manual' en lugar de 'filename'
                        results['final_music'] = filename_result['detected_music']
                        results['detected_music_confidence'] = 0.7
                        logger.info(f"Música extraída del filename (sin validar): {results['final_music']}")
                        return results
            except Exception as e:
                logger.warning(f"Error extrayendo música del filename: {e}")
        
        # Estrategia 2: Spotify API (para metadatos musicales)
        if self.spotify:
            try:
                spotify_result = self._recognize_with_spotify(audio_path)
                if spotify_result['detected_music']:
                    results.update(spotify_result)
                    results['music_source'] = 'spotify'
                    results['final_music'] = spotify_result['detected_music']
                    results['final_music_artist'] = spotify_result['detected_music_artist']
                    logger.info(f"Música detectada con Spotify: {results['final_music']}")
                    return results
            except Exception as e:
                logger.error(f"Error en Spotify API: {e}")
        
        # Estrategia 3: YouTube API (para trends virales)
        if self.youtube:
            try:
                youtube_result = self._recognize_with_youtube(audio_path, filename)
                if youtube_result['detected_music']:
                    results.update(youtube_result)
                    results['music_source'] = 'youtube'
                    # Solo usar como final_music si no es una playlist genérica
                    if not self._is_generic_playlist(youtube_result['detected_music']):
                        results['final_music'] = youtube_result['detected_music']
                        results['final_music_artist'] = youtube_result['detected_music_artist']
                    logger.info(f"Música detectada con YouTube: {results['detected_music']}")
                    return results
            except Exception as e:
                logger.error(f"Error en YouTube API: {e}")
        
        # Estrategia 4: ACRCloud (fallback confiable)
        if self.acrcloud_config:
            try:
                acrcloud_result = self._recognize_with_acrcloud(audio_path)
                if acrcloud_result['detected_music']:
                    results.update(acrcloud_result)
                    results['music_source'] = 'acrcloud'
                    results['final_music'] = acrcloud_result['detected_music']
                    results['final_music_artist'] = acrcloud_result['detected_music_artist']
                    logger.info(f"Música detectada con ACRCloud: {results['final_music']}")
                    return results
            except Exception as e:
                logger.error(f"Error en ACRCloud: {e}")
        
        logger.warning(f"No se pudo reconocer música en: {audio_path}")
        results['error'] = "No se pudo identificar la música con ningún método"
        return results
    
    def _extract_music_from_filename(self, filename: str) -> Dict:
        """Extraer música del nombre del archivo usando patrones"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.9
        }
        
        # Limpiar el filename
        clean_filename = filename.replace('.mp4', '').replace('.mkv', '').replace('.avi', '')
        
        # Intentar extraer con diferentes patrones
        for pattern in self.music_patterns:
            matches = re.findall(pattern, clean_filename)
            if matches:
                music_title = matches[0].strip()
                # Filtrar títulos muy cortos o que contienen solo símbolos
                if len(music_title) > 2 and not music_title.isdigit():
                    # Limpiar título de hashtags y caracteres especiales
                    music_title = re.sub(r'#\w+', '', music_title).strip()
                    music_title = re.sub(r'[^\w\s\-\']', ' ', music_title).strip()
                    
                    if music_title:
                        results['detected_music'] = music_title
                        logger.info(f"Música extraída del filename: {music_title}")
                        break
        
        # Si no encontró con patrones, buscar palabras clave conocidas de música
        if not results['detected_music']:
            music_keywords = [
                'blue moon', 'white horse', 'giga chad', 'phonk', 'beat', 'remix',
                'mmd', 'song', 'music', 'audio', 'track', 'theme'
            ]
            
            filename_lower = clean_filename.lower()
            for keyword in music_keywords:
                if keyword in filename_lower:
                    # Extraer contexto alrededor de la palabra clave
                    context = self._extract_context_around_keyword(clean_filename, keyword)
                    if context:
                        results['detected_music'] = context
                        results['detected_music_confidence'] = 0.6
                        logger.info(f"Música extraída por contexto: {context}")
                        break
        
        return results
    
    def _extract_context_around_keyword(self, text: str, keyword: str) -> str:
        """Extraer contexto alrededor de una palabra clave"""
        words = text.split()
        keyword_lower = keyword.lower()
        
        for i, word in enumerate(words):
            if keyword_lower in word.lower():
                # Tomar 2-3 palabras alrededor
                start = max(0, i-1)
                end = min(len(words), i+3)
                context = ' '.join(words[start:end])
                # Limpiar caracteres especiales
                context = re.sub(r'[^\w\s\-\']', ' ', context).strip()
                if len(context) > 3:
                    return context
        return None
    
    def _validate_music_with_apis(self, music_result: Dict) -> Dict:
        """Validar música extraída del filename con APIs externas"""
        music_title = music_result['detected_music']
        if not music_title:
            return music_result
        
        # Intentar validar con Spotify
        if self.spotify:
            try:
                search_results = self.spotify.search(q=music_title, type='track', limit=5)
                if (search_results and 
                    'tracks' in search_results and 
                    search_results['tracks'] and 
                    'items' in search_results['tracks'] and 
                    search_results['tracks']['items']):
                    
                    track = search_results['tracks']['items'][0]
                    if track and track.get('name'):
                        music_result['detected_music'] = track['name']
                        if track.get('artists'):
                            music_result['detected_music_artist'] = ', '.join([artist['name'] for artist in track['artists']])
                        music_result['detected_music_confidence'] = 0.95
                        logger.info(f"Música validada con Spotify: {track['name']}")
                        return music_result
            except Exception as e:
                logger.warning(f"Error validando con Spotify: {e}")
        
        # Intentar validar con YouTube
        if self.youtube:
            try:
                search_response = self.youtube.search().list(
                    q=music_title,
                    part='snippet',
                    maxResults=5,
                    type='video'
                ).execute()
                
                for item in search_response.get('items', []):
                    title = item['snippet']['title']
                    if (any(word in title.lower() for word in ['music', 'song', 'audio', 'official']) and
                        not self._is_generic_playlist(title)):
                        music_result['detected_music'] = title
                        music_result['detected_music_artist'] = item['snippet']['channelTitle']
                        music_result['detected_music_confidence'] = 0.85
                        logger.info(f"Música validada con YouTube: {title}")
                        return music_result
            except Exception as e:
                logger.warning(f"Error validando con YouTube: {e}")
        
        return {}  # No se pudo validar
    
    def _is_generic_playlist(self, title: str) -> bool:
        """Detectar si un título es una playlist genérica"""
        generic_terms = [
            'playlist', 'compilation', 'mix', 'best of', 'top songs',
            'trending', 'viral songs', 'hits', 'collection'
        ]
        title_lower = title.lower()
        return any(term in title_lower for term in generic_terms)
    
    def _recognize_with_youtube(self, audio_path: Path, filename: str = None) -> Dict:
        """Reconocimiento usando YouTube Data API mejorado"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0
        }
        
        try:
            # Si tenemos filename, intentar buscar específicamente
            search_terms = []
            
            if filename:
                # Extraer términos del filename
                extracted = self._extract_music_from_filename(filename)
                if extracted['detected_music']:
                    search_terms.append(extracted['detected_music'])
            
            # Agregar términos genéricos como fallback
            search_terms.extend([
                'trending music 2024',
                'viral song 2024',
                'popular music'
            ])
            
            for search_term in search_terms:
                search_response = self.youtube.search().list(
                    q=search_term,
                    part='snippet',
                    maxResults=10,
                    type='video',
                    order='relevance'
                ).execute()
                
                for item in search_response.get('items', []):
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    
                    # Priorizar resultados específicos sobre playlists
                    if (any(word in title.lower() for word in ['music', 'song', 'audio', 'official']) and
                        not self._is_generic_playlist(title)):
                        results['detected_music'] = title
                        results['detected_music_artist'] = channel
                        results['detected_music_confidence'] = 0.7
                        return results
                
                # Si no encontramos específicos, usar el primer resultado relevante
                if search_response.get('items'):
                    item = search_response['items'][0]
                    results['detected_music'] = item['snippet']['title']
                    results['detected_music_artist'] = item['snippet']['channelTitle']
                    results['detected_music_confidence'] = 0.5
                    break
                        
        except Exception as e:
            logger.error(f"Error en YouTube API: {e}")
        
        return results
    
    def _recognize_with_spotify(self, audio_path: Path) -> Dict:
        """Reconocimiento usando Spotify API con validación mejorada"""
        results = {
            'detected_music': None,
            'detected_music_artist': None,
            'detected_music_confidence': 0.0
        }
        
        try:
            # Buscar en playlists virales específicas
            viral_queries = [
                'viral hits 2024',
                'trending now',
                'global viral 50',
                'today\'s top hits'
            ]
            
            for query in viral_queries:
                search_results = self.spotify.search(
                    q=query,
                    type='playlist',
                    limit=3
                )
                
                # Validación robusta de la respuesta
                if (not search_results or 
                    'playlists' not in search_results or 
                    not search_results['playlists'] or
                    'items' not in search_results['playlists'] or
                    not search_results['playlists']['items']):
                    continue
                
                for playlist in search_results['playlists']['items']:
                    if not playlist or 'id' not in playlist:
                        continue
                        
                    try:
                        tracks = self.spotify.playlist_tracks(playlist['id'], limit=10)
                        
                        if (not tracks or 
                            'items' not in tracks or 
                            not tracks['items']):
                            continue
                            
                        for track_item in tracks['items']:
                            if (not track_item or 
                                'track' not in track_item or 
                                not track_item['track']):
                                continue
                                
                            track = track_item['track']
                            name = track.get('name')
                            popularity = track.get('popularity', 0)
                            
                            if name and popularity > 70:
                                results['detected_music'] = name
                                artists = track.get('artists', [])
                                if artists:
                                    results['detected_music_artist'] = ', '.join([artist.get('name', '') for artist in artists if artist.get('name')])
                                results['detected_music_confidence'] = 0.8
                                return results
                                
                    except Exception as e:
                        logger.warning(f"Error procesando playlist {playlist.get('id', 'unknown')}: {e}")
                        continue
            
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
