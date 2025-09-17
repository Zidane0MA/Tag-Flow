import React from 'react';

// ==========================================
// SIDEBAR ICONS - Main app navigation
// ==========================================
export const SIDEBAR_NAVIGATION_ICONS = {
    gallery: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
    admin: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
    trash: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>,
};

// ==========================================
// THUMBNAIL AREA ICONS - Post thumbnail section (área superior)
// ==========================================

// Indicadores de Tipo de Contenido
export const CONTENT_TYPE_INDICATORS = {
    image: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" /></svg>,
};

// Indicadores de Estado de Edición
export const EDIT_STATUS_INDICATORS = {
    status_pending: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.25 6h1.5v6h-1.5V6zm0 7h1.5v1.5h-1.5V13z" clipRule="evenodd" /></svg>,
    status_in_progress: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.415L11 9.586V6z" clipRule="evenodd" /></svg>,
    status_completed: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>,
    close: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 23" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>,
};

// Indicadores de Estado de Proceso
export const PROCESS_STATUS_INDICATORS = {
    check_plain: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>,
    spinner: <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>,
    exclamation_simple: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 23" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 6v8m0 4h.01" /></svg>,
    close_error: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 23" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>,
};

// Botones de Acción (hover)
export const HOVER_ACTION_BUTTONS = {
    play: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>,
    edit: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>,
    analyze: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 2.5a.75.75 0 0 1 .75.75V5h1.75a.75.75 0 0 1 0 1.5H10.75v1.75a.75.75 0 0 1-1.5 0V6.5H7.5a.75.75 0 0 1 0-1.5H9.25V3.25A.75.75 0 0 1 10 2.5ZM5.25 5.5a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5H6a.75.75 0 0 1-.75-.75Zm9.5 0a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5h-1.75a.75.75 0 0 1-.75-.75Zm-5 4a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5H10a.75.75 0 0 1-.75-.75ZM2.75 11.5a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5H3.5a.75.75 0 0 1-.75-.75Zm14 0a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5h-1.75a.75.75 0 0 1-.75-.75Zm-9.5 4a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5H8a.75.75 0 0 1-.75-.75Zm-2-4a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5H6a.75.75 0 0 1-.75-.75Zm7 0a.75.75 0 0 1 .75-.75h1.75a.75.75 0 0 1 0 1.5h-1.75a.75.75 0 0 1-.75-.75Z" clipRule="evenodd" /></svg>,
    folder: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
    delete: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clipRule="evenodd" /></svg>,
};

// ==========================================
// INFORMATION AREA ICONS - Post information section (área inferior)
// ==========================================

// Cabecera
export const HEADER_ICONS = {
    external_link: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" /><path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" /></svg>,
};

// Información del Creador
export const CREATOR_ICONS = {
    user: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>,
};

// Iconos para Tipos de Suscripción (subscription_type)
export const SUBSCRIPTION_TYPE_ICONS = {
    // Database subscription types: account, playlist, hashtag, location, music, search, liked, saved, folder, watch_later
    user: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>,
    list: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" /></svg>,
    hashtag: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9.243 3.03a1 1 0 01.727 1.213L9.53 6h2.94l.26-1.757a1 1 0 111.959-.292L14.47 6H17a1 1 0 110 2h-2.18l-.26 1.757a1 1 0 11-1.96.292l.26-1.757H10.47l-.26 1.757a1 1 0 11-1.96.292l.26-1.757H6a1 1 0 110-2h2.18l.26-1.757a1 1 0 011.213-.727zM10.47 8l.26-1.757H7.79l-.26 1.757h2.94zm-1.177 4h2.94l.26-1.757H9.55l-.26 1.757z" clipRule="evenodd" /></svg>,
    location_marker: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 20l-4.95-6.05a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>,
    music: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V7.82l8-1.6v5.894A4.369 4.369 0 0015 12c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V3z" /></svg>,
    heart: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" /></svg>,
    bookmark: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" /></svg>,
    clock: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.415L11 9.586V6z" clipRule="evenodd" /></svg>,
    search: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" /></svg>,
    liked: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" /></svg>,
    saved: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" /></svg>,
    folder: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
    watch_later: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.415L11 9.586V6z" clipRule="evenodd" /></svg>,
};

// Iconos para Tipos de Categoría (category_type)
export const CATEGORY_TYPE_ICONS = {
    // Database category types: videos, shorts, feed, reels, stories, highlights, tagged
    video: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2.5a.5.5 0 01.5-.5h1a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-1a.5.5 0 01-.5-.5v-1zM7.5 9a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h1a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-1zm-.5 3.5a.5.5 0 01.5-.5h1a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-1a.5.5 0 01-.5-.5v-1zM11.5 5a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h1a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-1zm-.5 3.5a.5.5 0 01.5-.5h1a.5.5 0 01.5.5v1a.5.5 0 01-.5.5h-1a.5.5 0 01-.5-.5v-1zM11.5 13a.5.5 0 00-.5.5v1a.5.5 0 00.5.5h1a.5.5 0 00.5-.5v-1a.5.5 0 00-.5-.5h-1z" clipRule="evenodd" /></svg>,
    rack: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" /></svg>,
    shorts: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7 2a2 2 0 00-2 2v12a2 2 0 002 2h6a2 2 0 002-2V4a2 2 0 00-2-2H7zM8 16a1 1 0 100 2h4a1 1 0 100-2H8z" clipRule="evenodd" /></svg>,
    grid: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" clipRule="evenodd" /></svg>,
    reels: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2h6v4H7V5zm0 6h6v2H7v-2z" clipRule="evenodd" /></svg>,
    stories: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 2a3 3 0 00-3 3v10a3 3 0 003 3h10a3 3 0 003-3V5a3 3 0 00-3-3H5zm0 2h10a1 1 0 011 1v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1zm4 1a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>,
    highlights: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1.06-5.06a.75.75 0 01-1.062-1.062l3.5-3.5a.75.75 0 111.062 1.062l-3.5 3.5zm3.122-4.438a.75.75 0 10-1.06-1.06l-3.5 3.5a.75.75 0 101.06 1.06l3.5-3.5z" clipRule="evenodd" /></svg>,
    tag: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M17.707 9.293l-5-5a1 1 0 00-.707-.293H4a1 1 0 00-1 1v8a1 1 0 001 1h8c.265 0 .52-.105.707-.293l5-5a1 1 0 000-1.414zM7 9a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>,
};

// Información Adicional
export const ADDITIONAL_INFO_ICONS = {
    music: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V7.82l8-1.6v5.894A4.369 4.369 0 0015 12c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V3z" /></svg>,
    users: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>,
    notes: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" /><path fillRule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" /></svg>,
};

// Metadatos Secundarios
export const METADATA_ICONS = {
    clock: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.415L11 9.586V6z" clipRule="evenodd" /></svg>,
    file_alt: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" /></svg>,
    calendar: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" /></svg>,
};

// ==========================================
// UTILITY AND SYSTEM ICONS - Utilities and general system icons
// ==========================================
export const UTILITY_ICONS = {
    restore: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/></svg>,
    wrench: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>,
    terminal: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14" /></svg>,
    database: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V7M4 7c0-1.1.9-2 2-2h12c1.1 0 2 .9 2 2M4 7h16M12 11v6" /><ellipse cx="12" cy="7" rx="9" ry="2" /></svg>,
    hardDrive: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M22 11.08V12a10 10 0 11-5.93-9.14" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M22 4L12 14.01l-3-3" /></svg>,
    bolt: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
    chevronDown: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" /></svg>,
    chevronRight: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" /></svg>,
    plus: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" /></svg>,
};

// ==========================================
// CONSOLIDATED ICONS OBJECT - All icons in one place for backward compatibility
// ==========================================
export const ICONS = {
    // Sidebar Navigation
    ...SIDEBAR_NAVIGATION_ICONS,
    // Thumbnail Area
    ...CONTENT_TYPE_INDICATORS,
    ...EDIT_STATUS_INDICATORS,
    ...PROCESS_STATUS_INDICATORS,
    ...HOVER_ACTION_BUTTONS,
    // Information Area
    ...HEADER_ICONS,
    ...CREATOR_ICONS,
    ...SUBSCRIPTION_TYPE_ICONS,
    ...CATEGORY_TYPE_ICONS,
    ...ADDITIONAL_INFO_ICONS,
    ...METADATA_ICONS,
    // Utilities
    ...UTILITY_ICONS,
};

// ==========================================
// NAVIGATION LINKS - Main app navigation
// ==========================================
export const NAV_LINKS = [
    { name: 'Galería', href: '/gallery', icon: SIDEBAR_NAVIGATION_ICONS.gallery },
    { name: 'Administración', href: '/admin', icon: SIDEBAR_NAVIGATION_ICONS.admin },
    { name: 'Papelera', href: '/trash', icon: SIDEBAR_NAVIGATION_ICONS.trash },
];

// ==========================================
// SUBSCRIPTION ICON MAPPINGS - Based on database subscription_type
// ==========================================
export const SUBSCRIPTION_ICONS = {
    'account': SUBSCRIPTION_TYPE_ICONS.user,      // 👤
    'playlist': SUBSCRIPTION_TYPE_ICONS.list,     // 📋
    'music': SUBSCRIPTION_TYPE_ICONS.music,       // 🎵
    'hashtag': SUBSCRIPTION_TYPE_ICONS.hashtag,   // #️⃣
    'location': SUBSCRIPTION_TYPE_ICONS.location_marker, // 📍
    'saved': SUBSCRIPTION_TYPE_ICONS.saved,       // 💾
    'search': SUBSCRIPTION_TYPE_ICONS.search,     // 🔍
    'liked': SUBSCRIPTION_TYPE_ICONS.liked,       // 👍 (Default: YouTube thumbs up, use getSubscriptionIcon(type, platform) for platform-specific)
    'watch_later': SUBSCRIPTION_TYPE_ICONS.watch_later, // ⏰
    'folder': SUBSCRIPTION_TYPE_ICONS.folder,     // 📁
};

// ==========================================
// CATEGORY ICON MAPPINGS - Based on database category_type
// ==========================================
export const CATEGORY_ICONS = {
    'videos': CATEGORY_TYPE_ICONS.video,          // 🎬 Videos regulares (Default: standard video, use getCategoryIcon(type, platform) for TikTok rack)
    'shorts': CATEGORY_TYPE_ICONS.shorts,         // 📱 Videos cortos/verticales
    'feed': CATEGORY_TYPE_ICONS.grid,             // 🗂️ Instagram feed (rejilla)
    'reels': CATEGORY_TYPE_ICONS.reels,           // 🎞️ Instagram reels
    'stories': CATEGORY_TYPE_ICONS.stories,       // 📖 Instagram stories
    'highlights': CATEGORY_TYPE_ICONS.highlights, // ⭐ Instagram highlights
    'tagged': CATEGORY_TYPE_ICONS.tag,            // 🏷️ Instagram tagged
};

// ==========================================
// HELPER FUNCTIONS - Icon retrieval utilities
// ==========================================

// Function to get subscription icon with platform-specific handling
export const getSubscriptionIcon = (type: string, platform?: string) => {
    // Handle special case for 'liked' based on platform
    if (type === 'liked') {
        if (platform === 'youtube') {
            return SUBSCRIPTION_TYPE_ICONS.liked; // 👍 Thumbs up for YouTube
        } else if (platform === 'tiktok' || platform === 'instagram') {
            return SUBSCRIPTION_TYPE_ICONS.heart; // ❤️ Heart for TikTok/Instagram
        }
        // Default to liked (thumbs up) if no platform specified
        return SUBSCRIPTION_TYPE_ICONS.liked;
    }

    return SUBSCRIPTION_ICONS[type as keyof typeof SUBSCRIPTION_ICONS] || SUBSCRIPTION_TYPE_ICONS.folder;
};

// Function to get category icon with platform-specific handling
export const getCategoryIcon = (type: string, platform?: string) => {
    // Handle special case for 'videos' based on platform
    if (type === 'videos') {
        if (platform === 'tiktok') {
            return CATEGORY_TYPE_ICONS.rack; // 📊 Rack for TikTok videos
        }
        // Default to video icon for all other platforms
        return CATEGORY_TYPE_ICONS.video;
    }

    return CATEGORY_ICONS[type as keyof typeof CATEGORY_ICONS] || CATEGORY_TYPE_ICONS.video;
};

// ==========================================
// FRONTEND SECTION CATEGORIES - For showcase organized by frontend areas
// ==========================================
export const FRONTEND_ICON_CATEGORIES = {
    '🧭 Sidebar - Navegación Principal': SIDEBAR_NAVIGATION_ICONS,
    '🖼️ Thumbnail - Indicadores de Tipo': CONTENT_TYPE_INDICATORS,
    '📝 Thumbnail - Estados de Edición': EDIT_STATUS_INDICATORS,
    '⚡ Thumbnail - Estados de Proceso': PROCESS_STATUS_INDICATORS,
    '🎬 Thumbnail - Botones de Acción (Hover)': HOVER_ACTION_BUTTONS,
    '🔗 Información - Cabecera': HEADER_ICONS,
    '👤 Información - Creador': CREATOR_ICONS,
    '📋 Información - Tipos de Suscripción': SUBSCRIPTION_TYPE_ICONS,
    '🎞️ Información - Tipos de Categoría': CATEGORY_TYPE_ICONS,
    '🎵 Información - Adicional': ADDITIONAL_INFO_ICONS,
    '📊 Información - Metadatos': METADATA_ICONS,
    '🔧 Utilidades y Sistema': UTILITY_ICONS,
};