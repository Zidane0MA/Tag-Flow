import React, { useState } from 'react';
import { useAdminData } from '../../hooks/useAdminData';
import { ICONS } from '../../constants';
import { Operation, OperationStatus, OperationType } from '../../types/admin';
import Modal from '../../components/Modal';

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
    <div className="w-full bg-gray-700 rounded-full h-2.5">
        <div className="bg-red-600 h-2.5 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
    </div>
);

const OperationStatusBadge: React.FC<{ status: OperationStatus }> = ({ status }) => {
    const styles = {
        [OperationStatus.RUNNING]: 'bg-blue-500 text-white',
        [OperationStatus.COMPLETED]: 'bg-green-500 text-white',
        [OperationStatus.FAILED]: 'bg-red-500 text-white',
        [OperationStatus.CANCELLED]: 'bg-yellow-500 text-black',
        [OperationStatus.PENDING]: 'bg-gray-500 text-white',
    };
    return <span className={`px-2 py-1 text-xs font-bold rounded-full ${styles[status]}`}>{status}</span>;
}

const Section: React.FC<{ title: string, children: React.ReactNode}> = ({ title, children }) => (
    <div className="bg-gray-800/50 p-4 rounded-md">
        <h4 className="font-semibold text-red-400 mb-3">{title}</h4>
        <div className="space-y-3">{children}</div>
    </div>
);

const FormRow: React.FC<{ children: React.ReactNode }> = ({ children }) => <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-end">{children}</div>;
const FormField: React.FC<{ label: React.ReactNode, children: React.ReactNode }> = ({ label, children }) => (
    <div>
        <label className="text-sm font-medium text-gray-300 block mb-1">{label}</label>
        {children}
    </div>
);
const Input = (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} className="w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none" />;
const Select = (props: React.SelectHTMLAttributes<HTMLSelectElement>) => <select {...props} className="w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none" />;
const Checkbox: React.FC<{ label: string, checked: boolean, onChange: (e: React.ChangeEvent<HTMLInputElement>) => void }> = ({ label, ...props }) => (
    <label className="flex items-center gap-2 text-sm text-gray-300">
        <input type="checkbox" {...props} className="rounded text-red-600 bg-gray-600 border-gray-500 focus:ring-red-600" />
        {label}
    </label>
);
const ActionButton: React.FC<{ onClick: () => void, children: React.ReactNode }> = ({ onClick, children }) => (
    <button onClick={onClick} className="w-full sm:w-auto justify-center bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-4 rounded transition flex items-center gap-2">{children}</button>
);


const OperationsPage: React.FC = () => {
    const { operations, startOperation, cancelOperation } = useAdminData();
    const [activeTab, setActiveTab] = useState('video');
    
    // State for all forms
    const [videoParams, setVideoParams] = useState({ limit: 100, platform: 'all', source: 'all', videoIds: '', forceReanalysis: false });
    const [dbParams, setDbParams] = useState({ source: 'all', platform: 'all', limit: 1000, force: false, clearPlatform: 'all' });
    const [thumbParams, setThumbParams] = useState({ platform: 'all', limit: 100, forceRegenerate: false, forceClean: false });
    const [systemParams, setSystemParams] = useState({ compress: true, noThumbnails: false, thumbnailLimit: 1000, fixIssues: false, verifyFileId: '' });

    const [confirmingAction, setConfirmingAction] = useState<{type: OperationType, params: any} | null>(null);

    const handleActionWithConfirm = (type: OperationType, params: any, message: string) => {
        setConfirmingAction({type, params});
    };

    const executeConfirmedAction = () => {
        if (confirmingAction) {
            startOperation(confirmingAction.type, confirmingAction.params);
            setConfirmingAction(null);
        }
    };

    const activeOperations = operations.filter(op => op.status === OperationStatus.RUNNING);
    const historyOperations = operations.filter(op => op.status !== OperationStatus.RUNNING);

    const tabs = [
        { id: 'video', name: 'Videos' },
        { id: 'database', name: 'Base de Datos' },
        { id: 'thumbnail', name: 'Thumbnails' },
        { id: 'system', name: 'Sistema' },
    ];

    return (
        <div className="space-y-8">
            {confirmingAction && (
                <Modal isOpen={true} onClose={() => setConfirmingAction(null)} title="Confirmar Acción Peligrosa">
                    <p className="text-gray-300 mb-4">¿Estás seguro de que quieres ejecutar la operación <strong className="text-red-400">{confirmingAction.type}</strong>? Esta acción puede ser irreversible.</p>
                    <div className="flex justify-end gap-4">
                        <button onClick={() => setConfirmingAction(null)} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500">Cancelar</button>
                        <button onClick={executeConfirmedAction} className="px-4 py-2 bg-red-700 text-white rounded-md hover:bg-red-600">Confirmar y Ejecutar</button>
                    </div>
                </Modal>
            )}

            {/* Real-Time & History */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                <div className="lg:col-span-3 space-y-8">
                    <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                        <h3 className="font-bold text-white text-lg mb-4">Operaciones en Tiempo Real</h3>
                        {activeOperations.length > 0 ? (
                            <div className="space-y-4">
                                {activeOperations.map(op => (
                                    <div key={op.id} className="bg-gray-800/50 p-4 rounded-md">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-semibold">{op.type}</span>
                                            <button onClick={() => cancelOperation(op.id)} className="text-red-500 hover:text-red-400 text-sm">Cancelar</button>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-2">{op.message}</p>
                                        <ProgressBar progress={op.progress} />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 text-center py-4">No hay operaciones activas.</p>
                        )}
                    </div>

                    <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                        <h3 className="font-bold text-white text-lg mb-4">Historial de Operaciones</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left text-gray-300">
                                <thead className="text-xs text-gray-400 uppercase bg-gray-700/50">
                                    <tr>
                                        <th className="p-3">Tipo</th>
                                        <th className="p-3">Estado</th>
                                        <th className="p-3">Inicio</th>
                                        <th className="p-3">Comando</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {historyOperations.slice(0, 10).map(op => (
                                        <tr key={op.id} className="border-b border-gray-700 hover:bg-gray-800/50">
                                            <td className="p-3 font-medium">{op.type}</td>
                                            <td className="p-3"><OperationStatusBadge status={op.status}/></td>
                                            <td className="p-3">{new Date(op.startTime).toLocaleString()}</td>
                                            <td className="p-3 font-mono text-xs truncate" title={op.command}>{op.command}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Control Panel */}
                <div className="lg:col-span-2 bg-[#212121] p-6 rounded-lg shadow-lg h-fit">
                    <h3 className="font-bold text-white text-lg mb-4">Panel de Control</h3>
                    <div className="border-b border-gray-700 mb-4">
                        <nav className="-mb-px flex space-x-4 overflow-x-auto no-scrollbar" aria-label="Tabs">
                            {tabs.map(tab => (
                                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                                    className={`${activeTab === tab.id ? 'border-red-500 text-red-400' : 'border-transparent text-gray-400 hover:text-gray-200'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}>
                                    {tab.name}
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="space-y-6">
                        {activeTab === 'video' && (
                            <Section title="Operaciones de Video">
                                <FormRow>
                                    <FormField label={
                                        <div className="flex items-center gap-2">
                                            <span>Límite</span>
                                            <div className="relative group">
                                                <span className="text-gray-400 cursor-help">{React.cloneElement(ICONS.status_pending, { className: "h-4 w-4"})}</span>
                                                <div 
                                                    className="absolute bottom-full left-0 mb-2 w-72 bg-[#2d2d2d] text-gray-200 text-xs rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 border border-gray-600 shadow-xl">
                                                    <h4 className="font-bold mb-2 text-red-400">Comportamiento del --limit</h4>
                                                    <ul className="space-y-1.5 text-left">
                                                        <li className="flex gap-2 items-start">
                                                            <strong className="font-mono bg-gray-700 px-1.5 py-0.5 rounded text-red-400 text-[10px] w-12 text-center">0</strong> 
                                                            <span className="flex-1">Procesa solo los videos pendientes de la BD.</span>
                                                        </li>
                                                        <li className="flex gap-2 items-start">
                                                            <strong className="font-mono bg-gray-700 px-1.5 py-0.5 rounded text-red-400 text-[10px] w-12 text-center">N</strong> 
                                                            <span className="flex-1">Procesa hasta N videos. Si hay menos, puebla nuevos hasta alcanzar N y luego procesa el total.</span>
                                                        </li>
                                                        <li className="flex gap-2 items-start">
                                                            <strong className="font-mono bg-gray-700 px-1.5 py-0.5 rounded text-red-400 text-[10px] w-12 text-center">vacío</strong> 
                                                            <span className="flex-1">Puebla todos los videos nuevos y luego procesa todos los pendientes.</span>
                                                        </li>
                                                    </ul>
                                                    <div className="absolute w-3 h-3 bg-[#2d2d2d] border-r border-b border-gray-600 rotate-45 -bottom-1.5 left-4"></div>
                                                </div>
                                            </div>
                                        </div>
                                    }>
                                        <Input type="number" value={videoParams.limit} onChange={e => setVideoParams({...videoParams, limit: parseInt(e.target.value)})} />
                                    </FormField>
                                </FormRow>
                                <FormRow>
                                    <FormField label="Plataforma"><Select value={videoParams.platform} onChange={e => setVideoParams({...videoParams, platform: e.target.value})}><option value="all">Todas</option><option value="youtube">YouTube</option><option value="tiktok">TikTok</option></Select></FormField>
                                    <FormField label="Fuente"><Select value={videoParams.source} onChange={e => setVideoParams({...videoParams, source: e.target.value})}><option value="all">Todas</option><option value="db">Base de datos</option><option value="organized">Organizados</option></Select></FormField>
                                </FormRow>
                                <ActionButton onClick={() => startOperation(OperationType.PROCESS_VIDEOS, {limit: videoParams.limit, platform: videoParams.platform, source: videoParams.source})}>Iniciar Procesamiento</ActionButton>
                                <hr className="border-gray-600"/>
                                <FormField label="Reanalizar (IDs de video separados por coma)"><Input type="text" value={videoParams.videoIds} onChange={e => setVideoParams({...videoParams, videoIds: e.target.value})} /></FormField>
                                <Checkbox label="Forzar reanálisis" checked={videoParams.forceReanalysis} onChange={e => setVideoParams({...videoParams, forceReanalysis: e.target.checked})} />
                                <ActionButton onClick={() => startOperation(OperationType.ANALYZE_VIDEOS, {video_ids: videoParams.videoIds, force: videoParams.forceReanalysis})}>Iniciar Reanálisis</ActionButton>
                            </Section>
                        )}
                        {activeTab === 'database' && (
                            <Section title="Operaciones de Base de Datos">
                                <ActionButton onClick={() => startOperation(OperationType.OPTIMIZE_DB)}>Optimizar BD</ActionButton>
                                <hr className="border-gray-600"/>
                                <FormRow>
                                    <FormField label="Fuente"><Select value={dbParams.source} onChange={e => setDbParams({...dbParams, source: e.target.value})}><option value="all">Todas</option><option value="db">DB</option><option value="organized">Organizados</option></Select></FormField>
                                    <FormField label="Plataforma"><Select value={dbParams.platform} onChange={e => setDbParams({...dbParams, platform: e.target.value})}><option value="all">Todas</option><option value="youtube">YouTube</option><option value="tiktok">TikTok</option></Select></FormField>
                                </FormRow>
                                <FormRow>
                                    <FormField label={
                                        <div className="flex items-center gap-2">
                                            <span>Límite</span>
                                            <div className="relative group">
                                                <span className="text-gray-400 cursor-help">{React.cloneElement(ICONS.status_pending, { className: "h-4 w-4"})}</span>
                                                <div 
                                                    className="absolute bottom-full left-0 mb-2 w-64 bg-[#2d2d2d] text-gray-200 text-xs rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 border border-gray-600 shadow-xl">
                                                    <h4 className="font-bold mb-2 text-red-400">Comportamiento del --limit</h4>
                                                    <ul className="space-y-1.5 text-left">
                                                        <li className="flex gap-2 items-start">
                                                            <strong className="font-mono bg-gray-700 px-1.5 py-0.5 rounded text-red-400 text-[10px] w-12 text-center">N</strong> 
                                                            <span className="flex-1">Importa como máximo N videos nuevos.</span>
                                                        </li>
                                                        <li className="flex gap-2 items-start">
                                                            <strong className="font-mono bg-gray-700 px-1.5 py-0.5 rounded text-red-400 text-[10px] w-12 text-center">vacío</strong> 
                                                            <span className="flex-1">Importa todos los videos nuevos.</span>
                                                        </li>
                                                    </ul>
                                                    <div className="absolute w-3 h-3 bg-[#2d2d2d] border-r border-b border-gray-600 rotate-45 -bottom-1.5 left-4"></div>
                                                </div>
                                            </div>
                                        </div>
                                    }>
                                        <Input type="number" value={dbParams.limit} onChange={e => setDbParams({...dbParams, limit: parseInt(e.target.value)})} />
                                    </FormField>
                                </FormRow>
                                <ActionButton onClick={() => startOperation(OperationType.POPULATE_DB, {source: dbParams.source, platform: dbParams.platform, limit: dbParams.limit})}>Poblar BD</ActionButton>
                                <hr className="border-gray-600"/>
                                <FormField label="Plataforma a Limpiar"><Select value={dbParams.clearPlatform} onChange={e => setDbParams({...dbParams, clearPlatform: e.target.value})}><option value="all">Todas</option><option value="youtube">YouTube</option></Select></FormField>
                                <button onClick={() => handleActionWithConfirm(OperationType.CLEAR_DB, {platform: dbParams.clearPlatform}, 'Limpiar DB')} className="w-full sm:w-auto justify-center bg-yellow-600 hover:bg-yellow-500 text-white font-bold py-2 px-4 rounded transition flex items-center gap-2">Limpiar BD (Peligroso)</button>
                            </Section>
                        )}
                        {activeTab === 'thumbnail' && (
                           <Section title="Operaciones de Thumbnails">
                               <ActionButton onClick={() => startOperation(OperationType.THUMBNAIL_STATS)}>Ver Estadísticas</ActionButton>
                                <hr className="border-gray-600"/>
                                <FormRow>
                                     <FormField label="Límite"><Input type="number" value={thumbParams.limit} onChange={e => setThumbParams({...thumbParams, limit: parseInt(e.target.value)})} /></FormField>
                                     <FormField label="Plataforma"><Select value={thumbParams.platform} onChange={e => setThumbParams({...thumbParams, platform: e.target.value})}><option value="all">Todas</option><option value="youtube">YouTube</option></Select></FormField>
                                </FormRow>
                                <ActionButton onClick={() => startOperation(OperationType.POPULATE_THUMBNAILS, {limit: thumbParams.limit, platform: thumbParams.platform})}>Poblar Faltantes</ActionButton>
                                <hr className="border-gray-600"/>
                                <Checkbox label="Forzar Regeneración" checked={thumbParams.forceRegenerate} onChange={e => setThumbParams({...thumbParams, forceRegenerate: e.target.checked})} />
                                <ActionButton onClick={() => startOperation(OperationType.REGENERATE_THUMBNAILS, {force: thumbParams.forceRegenerate})}>Regenerar Todos</ActionButton>
                                <hr className="border-gray-600"/>
                                 <ActionButton onClick={() => startOperation(OperationType.CLEAN_THUMBNAILS, {})}>Limpiar Huérfanos</ActionButton>
                           </Section>
                        )}
                        {activeTab === 'system' && (
                            <Section title="Operaciones del Sistema">
                                <FormRow>
                                    <Checkbox label="Comprimir" checked={systemParams.compress} onChange={e => setSystemParams({...systemParams, compress: e.target.checked})}/>
                                    <Checkbox label="Sin Thumbnails" checked={systemParams.noThumbnails} onChange={e => setSystemParams({...systemParams, noThumbnails: e.target.checked})}/>
                                </FormRow>
                                <ActionButton onClick={() => startOperation(OperationType.BACKUP, {compress: systemParams.compress, no_thumbnails: systemParams.noThumbnails})}>Crear Backup</ActionButton>
                                <hr className="border-gray-600"/>
                                <Checkbox label="Arreglar Problemas" checked={systemParams.fixIssues} onChange={e => setSystemParams({...systemParams, fixIssues: e.target.checked})}/>
                                <ActionButton onClick={() => startOperation(OperationType.VERIFY_SYSTEM, {fix: systemParams.fixIssues})}>Verificar Sistema</ActionButton>
                                <hr className="border-gray-600"/>
                                <ActionButton onClick={() => startOperation(OperationType.LIST_BACKUPS)}>Listar Backups</ActionButton>
                                <ActionButton onClick={() => handleActionWithConfirm(OperationType.CLEANUP_BACKUPS, {}, 'Limpiar Backups')}>Limpiar Backups</ActionButton>
                            </Section>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OperationsPage;