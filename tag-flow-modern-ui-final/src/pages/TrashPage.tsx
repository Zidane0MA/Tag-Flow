
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { useCursorTrashData } from '../hooks/useCursorTrashData';
import { useCursorCRUD } from '../hooks/useCursorCRUD';
import { apiService } from '../services/apiService';
import { Post } from '../types';
import { ICONS } from '../constants';
import TrashVideoCard from '../components/TrashVideoCard';
import BulkActionBar from '../components/BulkActionBar';
import Modal from '../components/Modal';
import PermanentDeleteModal from '../components/PermanentDeleteModal';
import Toast from '../components/Toast';

const timeAgo = (date: string | Date): string => {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return `hace ${Math.floor(interval)} años`;
    interval = seconds / 2592000;
    if (interval > 1) return `hace ${Math.floor(interval)} meses`;
    interval = seconds / 86400;
    if (interval > 1) return `hace ${Math.floor(interval)} días`;
    interval = seconds / 3600;
    if (interval > 1) return `hace ${Math.floor(interval)} horas`;
    interval = seconds / 60;
    if (interval > 1) return `hace ${Math.floor(interval)} minutos`;
    return `hace ${Math.floor(seconds)} segundos`;
};

const TrashPage: React.FC = () => {
    const {
        posts: trash,
        loading: trashLoading,
        loadingMore,
        error,
        scrollState,
        loadTrashVideos,
        loadMoreVideos,
        refreshData,
        clearData
    } = useCursorTrashData();
    const { restoreFromTrash, deletePermanently } = useCursorCRUD();
    const [selectedIds, setSelectedIds] = useState<string[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [sort, setSort] = useState({ by: 'deletedAt', order: 'desc' });
    const [currentPage, setCurrentPage] = useState(1);
    const [isConfirmingEmpty, setIsConfirmingEmpty] = useState(false);
    const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
    const [isConfirmingIndividualDelete, setIsConfirmingIndividualDelete] = useState(false);
    const [individualDeleteVideo, setIndividualDeleteVideo] = useState<Post | null>(null);
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState<{message: string, type: 'success' | 'error', visible: boolean}>({
        message: '',
        type: 'success',
        visible: false
    });

    const ITEMS_PER_PAGE = 12;

    const filteredAndSortedTrash = useMemo(() => {
        const filtered = trash.filter(post => 
            post.title.toLowerCase().includes(searchTerm.toLowerCase())
        );

        return filtered.sort((a, b) => {
            const aVal = a[sort.by as keyof Post] || 0;
            const bVal = b[sort.by as keyof Post] || 0;
            if (aVal < bVal) return sort.order === 'asc' ? -1 : 1;
            if (aVal > bVal) return sort.order === 'asc' ? 1 : -1;
            return 0;
        });
    }, [trash, searchTerm, sort]);

    const paginatedTrash = useMemo(() => {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        return filteredAndSortedTrash.slice(startIndex, startIndex + ITEMS_PER_PAGE);
    }, [filteredAndSortedTrash, currentPage]);

    const handleSelect = (id: string, isSelected: boolean) => {
        setSelectedIds(prev => isSelected ? [...prev, id] : prev.filter(pid => pid !== id));
    };

    const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.checked) {
            setSelectedIds(paginatedTrash.map(p => p.id));
        } else {
            setSelectedIds([]);
        }
    };
    
    const executeBulkAction = async (action: (id: string) => void, ids: string[]) => {
        setLoading(true);
        await Promise.all(ids.map(id => new Promise(resolve => setTimeout(() => { action(id); resolve(true); }, 50)))); // Simulate delay
        setSelectedIds([]);
        setLoading(false);
    };

    const handleRestoreSelected = async () => {
        setLoading(true);
        try {
            await apiService.restoreMultipleVideos(selectedIds);
            await refreshData(); // Refresh the trash data
            setSelectedIds([]);
        } catch (error) {
            console.error('Error restoring selected videos:', error);
        } finally {
            setLoading(false);
        }
    };
    const handleDeleteSelected = () => setIsConfirmingDelete(true);
    const handleEmptyTrash = () => setIsConfirmingEmpty(true);
    
    const confirmDeleteSelected = async () => {
        setIsConfirmingDelete(false);
        setLoading(true);
        
        try {
            // Delete each video individually to get success messages
            const results = await Promise.all(
                selectedIds.map(id => deletePermanently(id))
            );
            
            const successCount = results.filter(r => r.success).length;
            setToast({
                message: `${successCount} videos eliminados permanentemente de la base de datos y movidos a la papelera del sistema`,
                type: 'success',
                visible: true
            });
            
            setSelectedIds([]);
        } catch (error) {
            setToast({
                message: 'Error al eliminar videos permanentemente',
                type: 'error',
                visible: true
            });
        } finally {
            setLoading(false);
        }
    };

    const handleIndividualDelete = (video: Post) => {
        setIndividualDeleteVideo(video);
        setIsConfirmingIndividualDelete(true);
    };

    const confirmIndividualDelete = async () => {
        if (!individualDeleteVideo) return;
        
        setIsConfirmingIndividualDelete(false);
        setLoading(true);
        
        try {
            const result = await deletePermanently(individualDeleteVideo.id);
            
            if (result.success && result.message) {
                setToast({
                    message: result.message,
                    type: 'success',
                    visible: true
                });
            } else {
                setToast({
                    message: result.message || 'Error al eliminar el video permanentemente',
                    type: 'error',
                    visible: true
                });
            }
        } catch (error) {
            setToast({
                message: 'Error al eliminar el video permanentemente',
                type: 'error',
                visible: true
            });
        } finally {
            setLoading(false);
            setIndividualDeleteVideo(null);
        }
    };

    const confirmEmptyTrash = async () => {
        setIsConfirmingEmpty(false);
        setLoading(true);
        try {
            await apiService.emptyTrash();
            await refreshData(); // Refresh the trash data
        } catch (error) {
            console.error('Error emptying trash:', error);
        } finally {
            setLoading(false);
        }
    };

    // Load trash videos on mount
    useEffect(() => {
        loadTrashVideos();
    }, [loadTrashVideos]);

    const isAllSelected = paginatedTrash.length > 0 && selectedIds.length === paginatedTrash.length;

    return (
        <>
            <div className="space-y-6">
                <header className="flex flex-wrap justify-between items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Papelera</h1>
                        <p className="text-gray-400 mt-1">{trash.length} elementos eliminados</p>
                    </div>
                    {trash.length > 0 && (
                        <button onClick={handleEmptyTrash} disabled={loading} className="px-4 py-2 bg-red-800 hover:bg-red-700 text-white font-semibold rounded-md transition disabled:opacity-50 flex items-center gap-2">
                            {ICONS.delete} Vaciar Papelera
                        </button>
                    )}
                </header>

                {trash.length > 0 && (
                    <div className="p-4 bg-[#212121] rounded-lg flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                className="h-4 w-4 rounded text-red-600 bg-gray-900 border-gray-500 focus:ring-red-500"
                                checked={isAllSelected}
                                onChange={handleSelectAll}
                                title="Seleccionar todos en esta página"
                            />
                            <input
                                type="text"
                                placeholder="Buscar en la papelera..."
                                value={searchTerm}
                                onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                                className="w-full sm:w-64 bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-400">Ordenar por:</span>
                            <select value={sort.by} onChange={e => setSort(s => ({...s, by: e.target.value}))} className="bg-gray-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-red-500 focus:outline-none">
                                <option value="deletedAt">Fecha de eliminación</option>
                                <option value="title">Título</option>
                            </select>
                            <select value={sort.order} onChange={e => setSort(s => ({...s, order: e.target.value}))} className="bg-gray-700 text-white rounded p-2 text-sm focus:ring-2 focus:ring-red-500 focus:outline-none">
                                <option value="desc">Desc</option>
                                <option value="asc">Asc</option>
                            </select>
                        </div>
                    </div>
                )}
                
                <div className={selectedIds.length > 0 ? 'pb-24' : ''}>
                    {paginatedTrash.length > 0 ? (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {paginatedTrash.map(post => (
                                    <TrashVideoCard
                                        key={post.id}
                                        video={post}
                                        timeAgo={timeAgo(post.deletedAt || new Date())}
                                        isSelected={selectedIds.includes(post.id)}
                                        onSelect={handleSelect}
                                        onRestore={restoreFromTrash}
                                        onDelete={handleIndividualDelete}
                                    />
                                ))}
                            </div>
                             <Pagination 
                                currentPage={currentPage} 
                                totalItems={filteredAndSortedTrash.length} 
                                itemsPerPage={ITEMS_PER_PAGE} 
                                onPageChange={setCurrentPage} 
                            />
                        </>
                    ) : (
                        <div className="text-center py-20 bg-[#181818] rounded-lg">
                            <div className="text-gray-500 mb-4">{React.cloneElement(ICONS.trash, {className: "h-16 w-16 mx-auto"})}</div>
                            <h3 className="text-2xl font-semibold text-white">La papelera está vacía</h3>
                            <p className="text-gray-400 mt-2">Los elementos eliminados de la galería aparecerán aquí.</p>
                        </div>
                    )}
                </div>
            </div>

            <BulkActionBar
                isVisible={selectedIds.length > 0}
                selectedCount={selectedIds.length}
                onRestore={handleRestoreSelected}
                onDelete={handleDeleteSelected}
                onClear={() => setSelectedIds([])}
                isLoading={loading}
            />

            <Modal isOpen={isConfirmingEmpty} onClose={() => setIsConfirmingEmpty(false)} title="Confirmar Vaciar Papelera">
                <p className="text-gray-300 mb-6">¿Estás seguro de que quieres eliminar permanentemente todos los {trash.length} elementos de la papelera? Esta acción no se puede deshacer.</p>
                <div className="flex justify-end gap-4">
                    <button onClick={() => setIsConfirmingEmpty(false)} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500">Cancelar</button>
                    <button onClick={confirmEmptyTrash} className="px-4 py-2 bg-red-800 text-white rounded-md hover:bg-red-700">Vaciar Papelera</button>
                </div>
            </Modal>
            
            {/* Bulk Delete Modal */}
            <PermanentDeleteModal
                isOpen={isConfirmingDelete}
                onClose={() => setIsConfirmingDelete(false)}
                onConfirm={confirmDeleteSelected}
                videoTitle=""
                isMultiple={true}
                count={selectedIds.length}
            />
            
            {/* Individual Delete Modal */}
            <PermanentDeleteModal
                isOpen={isConfirmingIndividualDelete}
                onClose={() => {
                    setIsConfirmingIndividualDelete(false);
                    setIndividualDeleteVideo(null);
                }}
                onConfirm={confirmIndividualDelete}
                videoTitle={individualDeleteVideo?.title || ""}
                isMultiple={false}
            />
            
            <Toast
                message={toast.message}
                type={toast.type}
                isVisible={toast.visible}
                onClose={() => setToast(prev => ({ ...prev, visible: false }))}
            />
        </>
    );
};

export default TrashPage;
