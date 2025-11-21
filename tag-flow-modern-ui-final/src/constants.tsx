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
    list: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path clipRule="evenodd" d="M3.75 5c-.414 0-.75.336-.75.75s.336.75.75.75h16.5c.414 0 .75-.336.75-.75S20.664 5 20.25 5H3.75Zm0 4c-.414 0-.75.336-.75.75s.336.75.75.75h16.5c.414 0 .75-.336.75-.75S20.664 9 20.25 9H3.75Zm0 4c-.414 0-.75.336-.75.75s.336.75.75.75h8.5c.414 0 .75-.336.75-.75s-.336-.75-.75-.75h-8.5Zm8.5 4c.414 0 .75.336.75.75s-.336.75-.75.75h-8.5c-.414 0-.75-.336-.75-.75s.336-.75.75-.75h8.5Zm3.498-3.572c-.333-.191-.748.05-.748.434v6.276c0 .384.415.625.748.434L22 17l-6.252-3.572Z" fillRule="evenodd"/></svg>,
    hashtag: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M21.000,10.125a1.125,1.125,0,0,0,0.000,-2.250H16.893l0.713,-3.924a1.125,1.125,0,0,0,-2.214,-0.402L14.607,7.875H10.893l0.713,-3.924a1.125,1.125,0,0,0,-2.214,-0.402L8.607,7.875H4.091a1.125,1.125,0,1,0,0.000,2.250H8.197L7.516,13.875H3.000a1.125,1.125,0,0,0,0.000,2.250H7.107l-0.713,3.924a1.125,1.125,0,1,0,2.214,0.402L9.393,16.125h3.713l-0.713,3.924a1.125,1.125,0,1,0,2.214,0.402L15.393,16.125h4.516a1.125,1.125,0,1,0,0.000,-2.250H15.803l0.682,-3.750Zm-7.484,3.750H9.803l0.682,-3.750h3.713Z"/></svg>,
    location_marker: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 20l-4.95-6.05a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>,
    music: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V7.82l8-1.6v5.894A4.369 4.369 0 0015 12c-1.657 0-3 1.343-3 3s1.343 3 3 3 3-1.343 3-3V3z" /></svg>,
    heart: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" /></svg>,
    search: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" /></svg>,
    liked: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" /></svg>,
    saved: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" /></svg>,
    folder: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>,
    watch_later: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm1-13h-2v6l5.25 3.15.75-1.23L13 11.5V7z"/></svg>,
};

// Iconos para Tipos de Categoría (category_type)
export const CATEGORY_TYPE_ICONS = {
    // Database category types: videos, shorts, feed, reels, stories, highlights, tagged
    video: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path clipRule="evenodd" d="M3.5 5.5h17v13h-17v-13ZM2 5.5C2 4.672 2.672 4 3.5 4h17c.828 0 1.5.672 1.5 1.5v13c0 .828-.672 1.5-1.5 1.5h-17c-.828 0-1.5-.672-1.5-1.5v-13Zm7.748 2.927c-.333-.19-.748.05-.748.435v6.276c0 .384.415.625.748.434L16 12 9.748 8.427Z" fillRule="evenodd"/></svg>,
    rack: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="3" width="2" height="8" rx="1"/><rect x="11" y="3" width="2" height="8" rx="1"/><rect x="17" y="3" width="2" height="8" rx="1"/><rect x="5" y="13" width="2" height="8" rx="1"/><rect x="11" y="13" width="2" height="8" rx="1"/><rect x="17" y="13" width="2" height="8" rx="1"/></svg>,
    shorts: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path clipRule="evenodd" d="M18.45 8.851c1.904-1.066 2.541-3.4 1.422-5.214-1.119-1.814-3.57-2.42-5.475-1.355L5.55 7.247c-1.29.722-2.049 2.069-1.968 3.491.081 1.423.989 2.683 2.353 3.268l.942.404-1.327.742c-1.904 1.066-2.541 3.4-1.422 5.214 1.119 1.814 3.57 2.421 5.475 1.355l8.847-4.965c1.29-.722 2.049-2.068 1.968-3.49-.081-1.423-.989-2.684-2.353-3.269l-.942-.403 1.327-.743ZM10 14.567a.25.25 0 00.374.217l4.45-2.567a.25.25 0 000-.433l-4.45-2.567a.25.25 0 00-.374.216v5.134Z" fillRule="evenodd"/></svg>,
    grid: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h18v18H3zm6.015 0v18m5.97-18v18M21 9.015H3m18 5.97H3"/></svg>,
    reels: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><g stroke="currentColor" strokeLinejoin="round" strokeWidth="2" fill="none"><path d="M2.05 7.002h19.9"/><path strokeLinecap="round" d="m13.504 2.001 2.858 5.001M7.207 2.11l2.795 4.892M2 12.001v3.449c0 2.849.698 4.006 1.606 4.945.94.908 2.098 1.607 4.946 1.607h6.896c2.848 0 4.006-.699 4.946-1.607.908-.939 1.606-2.096 1.606-4.945V8.552c0-2.848-.698-4.006-1.606-4.945C19.454 2.699 18.296 2 15.448 2H8.552c-2.848 0-4.006.699-4.946 1.607C2.698 4.546 2 5.704 2 8.552z"/></g><path d="M9.763 17.664a.91.91 0 0 1-.454-.787V11.63a.91.91 0 0 1 1.364-.788l4.545 2.624a.91.91 0 0 1 0 1.575l-4.545 2.624a.91.91 0 0 1-.91 0z" fillRule="evenodd"/></svg>,
    stories: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M11.74 2.17c-.44.16-.7.65-.51 1.1.17.79 1.82.42 3.18.9a8.28 8.28 0 0 1 5.75 8.51A8.5 8.5 0 0 1 18 17.6c-.54.8.45 1.76 1.2 1.12a10.1 10.1 0 0 0 2.47-4.8 9.97 9.97 0 0 0-1.16-6.9 9.98 9.98 0 0 0-5.89-4.54c-1.05-.27-2.55-.44-2.88-.31M5.7 4.46A9 9 0 0 0 4 6.23c-.73 1.19.8 1.75 1.31 1.05.14-.18.95-1.1 1.23-1.38.89-.72 0-1.87-.84-1.44"/><path d="M11.24 7.95a28 28 0 0 0-.08 3.2c-.76 0-2.87.03-3 .05-.75.08-1.16 1.16-.22 1.62l3.22.03c0 1.46 0 3.07.1 3.27a.83.83 0 0 0 1.48 0c.1-.2.1-1.81.1-3.28 1.46 0 3.11 0 3.28-.09.6-.3.59-1.15 0-1.47-.2-.1-1.8-.11-3.28-.13 0-1.57-.01-3.2-.22-3.43s-1.03-.53-1.38.22m-8.5.64a9.5 9.5 0 0 0-.6 3.67c-.05 1.09 1.49 1.26 1.62.28.04-.92.35-2.9.5-3.4.2-1.1-1.2-1.4-1.5-.4m1.5 6.1c-.7-.9-1.6 0-1.5.5.1 1.3 2.0 3.8 3.3 4.6.5.4 1.76-.28 1.04-1.26-2.2-2.2-2.6-3.5-2.8-3.8m12.07 4.31c-2.4.9-4.4 1.6-7 .7-1.0-.5-1.9.8-.9 1.4 1.8.9 5.8 1.1 8.7-.7.4-.3.4-1.6-.7-1.4"/></svg>,
    highlights: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M11.3 3.47c-.62.05-1.29.16-1.83.32-.34.1-.45.16-.55.32-.16.27-.07.61.21.78.17.1.29.1.64 0 .75-.21 1.38-.3 2.13-.3.62 0 1.07.05 1.66.18.91.2 1.74.54 2.52 1.04.56.36.94.68 1.45 1.2.33.35.53.59.78.96.67.99 1.07 1.99 1.27 3.14.13.79.12 1.89-.03 2.66-.24 1.26-.72 2.32-1.51 3.37-.24.32-.29.43-.27.62.04.31.33.54.65.5.17-.02.24-.07.44-.32a8.94 8.94 0 0 0 1.85-6.87c-.27-1.89-1.15-3.63-2.53-5.01a8.8 8.8 0 0 0-5.32-2.56c-.39-.04-1.21-.06-1.57-.04zM6.34 5.42c-.23.11-1.02.86-1.12 1.07-.2.41.05.83.45.83.08 0 .18-.02.23-.04s.22-.17.41-.36c.18-.18.41-.4.51-.48.23-.19.29-.32.27-.54-.01-.08-.03-.19-.05-.24-.13-.25-.47-.36-.74-.23zM4.19 8.21c-.13.04-.24.11-.3.21-.08.13-.32.72-.44 1.08-.2.58-.33 1.17-.42 1.81-.04.32-.02.44.12.58.17.18.36.23.58.16.25-.07.38-.26.42-.59.08-.69.34-1.63.62-2.26.18-.39.18-.63.02-.83-.13-.16-.4-.23-.61-.16zm5.78.84c-.49.11-.91.38-1.23.79-.15.2-.34.61-.41.9-.06.22-.06.28-.06.67 0 .37.01.46.06.68.16.7.53 1.4 1.12 2.14.3.37 1.1 1.18 1.51 1.52.58.48.82.65.91.65.11 0 .14-.02.42-.25.66-.51 1.36-1.16 1.8-1.66.72-.83 1.18-1.68 1.34-2.45.05-.26.07-.76.03-1-.06-.56-.31-1.09-.66-1.45s-.85-.56-1.38-.56c-.69 0-1.19.31-1.47.92l-.08.17-.06-.14c-.27-.62-.8-.96-1.48-.96-.11 0-.28.02-.37.04zm-6.55 4.08c-.11.05-.23.16-.29.28-.09.18-.05.53.1 1.27.24.91.66 1.84 1.17 2.61.25.38.64.46.92.18.13-.13.19-.25.17-.45-.01-.14-.02-.17-.15-.41-.57-.9-.91-1.76-1.12-2.85-.08-.41-.14-.51-.36-.61a.7.7 0 0 0-.45-.02zm2.69 4.89c-.24.07-.4.29-.4.57 0 .2.06.3.34.53.92.8 2.09 1.45 3.23 1.8.5.15.69.15.89-.03.14-.12.18-.22.18-.4 0-.29-.16-.49-.46-.57-.34-.1-.83-.28-1.07-.38-.67-.28-1.43-.76-1.95-1.21-.33-.3-.53-.38-.76-.32zm10.25.75c-.04.02-.18.1-.31.18-.51.32-.99.56-1.46.72-.84.3-1.55.44-2.43.48-.45.02-.55.05-.7.21-.24.27-.16.69.17.87.12.07.12.07.47.06 1.51-.03 3.1-.49 4.4-1.27.42-.26.48-.31.57-.48.15-.3.07-.57-.22-.74-.13-.08-.38-.1-.49-.04z"/></svg>,
    tagged: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M10.201 3.797 12 1.997l1.799 1.8a1.59 1.59 0 0 0 1.124.465h5.259A1.818 1.818 0 0 1 22 6.08v14.104a1.818 1.818 0 0 1-1.818 1.818H3.818A1.818 1.818 0 0 1 2 20.184V6.08a1.818 1.818 0 0 1 1.818-1.818h5.26a1.59 1.59 0 0 0 1.123-.465z" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"/><g stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"><path d="M18.598 22.002V21.4a3.949 3.949 0 0 0-3.948-3.949H9.495A3.949 3.949 0 0 0 5.546 21.4v.603" fill="none"/><circle cx="12.07211" cy="11.07515" r="3.55556" fill="none"/></g></svg>,
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
    filter: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>,
    sort_asc: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" /></svg>,
    sort_desc: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4h13M3 8h9m-9 4h5m4 0v12m0 0l-4-4m4 4l4-4" /></svg>,
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
    'liked': SUBSCRIPTION_TYPE_ICONS.liked,       // 👍
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
    'tagged': CATEGORY_TYPE_ICONS.tagged,            // 🏷️ Instagram tagged
};

// ==========================================
// HELPER FUNCTIONS - Icon retrieval utilities
// ==========================================

// Function to get subscription icon with platform-specific handling
export const getSubscriptionIcon = (type: string, platform?: string) => {
    // Handle special case for 'liked' based on platform
    if (type === 'liked') {
        if (platform === 'youtube') {
            return SUBSCRIPTION_TYPE_ICONS.liked; // 👍 Heart for Youtube
        }
        // Default to liked for all other platforms
        return SUBSCRIPTION_TYPE_ICONS.heart;
    }

    return SUBSCRIPTION_ICONS[type as keyof typeof SUBSCRIPTION_ICONS];
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