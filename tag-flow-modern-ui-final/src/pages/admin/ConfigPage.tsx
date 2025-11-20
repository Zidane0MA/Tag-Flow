import React, { useState, useEffect } from 'react';
import { useAdminData } from '../../hooks/useAdminData';
import { ICONS } from '../../constants';
import { AdminConfig } from '../../types/admin';

const ConfigInput: React.FC<React.InputHTMLAttributes<HTMLInputElement> & { label: string, category: keyof AdminConfig, name: string, onChange: (e: React.ChangeEvent<HTMLInputElement>) => void }> = ({ label, ...props }) => (
    <div>
        <label className="block text-sm font-medium text-gray-300">{label}</label>
        <input {...props} data-category={props.category} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"/>
    </div>
);

const ToggleSwitch: React.FC<{ label: string; checked: boolean; onChange: (checked: boolean) => void; }> = ({ label, checked, onChange }) => (
    <label className="flex items-center justify-between cursor-pointer">
        <span className="text-sm font-medium text-gray-300">{label}</span>
        <div className="relative">
            <input type="checkbox" className="sr-only" checked={checked} onChange={(e) => onChange(e.target.checked)} />
            <div className={`block w-14 h-8 rounded-full ${checked ? 'bg-red-600' : 'bg-gray-600'}`}></div>
            <div className={`dot absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${checked ? 'transform translate-x-6' : ''}`}></div>
        </div>
    </label>
);


const ConfigPage: React.FC = () => {
    const { config, stats, updateConfig } = useAdminData();
    const [formData, setFormData] = useState(config);
    const [activeTab, setActiveTab] = useState('api');

    useEffect(() => {
        setFormData(config);
    }, [config]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type, dataset } = e.target;
        const category = dataset.category as keyof typeof formData;
        const isChecked = (e.target as HTMLInputElement).checked;

        if (category) {
            setFormData(prev => ({
                ...prev,
                [category]: {
                    ...prev[category],
                    [name]: type === 'checkbox' ? isChecked : value
                }
            }));
        }
    };
    
    const handleToggleChange = (name: string, category: keyof AdminConfig, isChecked: boolean) => {
         setFormData(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [name]: isChecked
            }
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        updateConfig(formData);
        alert('Configuración guardada!'); // Replace with a toast notification
    };

    const tabs = [
        { id: 'api', name: 'API Keys' },
        { id: 'paths', name: 'Rutas Externas' },
        { id: 'settings', name: 'Procesamiento' },
    ];
    
    const totalApis = Object.keys(config.apiKeys).length;
    const totalPaths = Object.keys(config.paths).length;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
                <div className="border-b border-gray-700">
                    <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`${
                                    activeTab === tab.id
                                        ? 'border-red-500 text-red-400'
                                        : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500'
                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                            >
                                {tab.name}
                            </button>
                        ))}
                    </nav>
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-8">
                    {activeTab === 'api' && (
                        <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                            <h3 className="text-lg font-bold text-white mb-4">Claves de API</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <ConfigInput label="YouTube API Key" type="password" name="youtube" category="apiKeys" value={formData.apiKeys.youtube} onChange={handleChange} />
                                <ConfigInput label="Spotify Client ID" type="text" name="spotifyClientId" category="apiKeys" value={formData.apiKeys.spotifyClientId} onChange={handleChange} />
                                <ConfigInput label="Spotify Client Secret" type="password" name="spotifyClientSecret" category="apiKeys" value={formData.apiKeys.spotifyClientSecret} onChange={handleChange} />
                                <ConfigInput label="ACRCloud Host" type="text" name="acrcloudHost" category="apiKeys" value={formData.apiKeys.acrcloudHost} onChange={handleChange} />
                                <ConfigInput label="ACRCloud Access Key" type="password" name="acrcloudAccessKey" category="apiKeys" value={formData.apiKeys.acrcloudAccessKey} onChange={handleChange} />
                                <ConfigInput label="ACRCloud Access Secret" type="password" name="acrcloudAccessSecret" category="apiKeys" value={formData.apiKeys.acrcloudAccessSecret} onChange={handleChange} />
                                <div className="md:col-span-2">
                                     <ConfigInput label="Google Credentials Path" type="text" name="googleCredentialsPath" category="apiKeys" value={formData.apiKeys.googleCredentialsPath} onChange={handleChange} placeholder="p. ej. /path/to/credentials.json" />
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'paths' && (
                        <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                            <h3 className="text-lg font-bold text-white mb-4">Rutas Externas</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <ConfigInput label="Ruta Base Organizada" name="organizedBasePath" category="paths" value={formData.paths.organizedBasePath} onChange={handleChange}/>
                                <div className="md:col-span-2 border-t border-gray-700 pt-4">
                                     <h4 className="text-md font-semibold text-gray-300 mb-2">Bases de Datos 4K Downloader</h4>
                                     <div className="space-y-4">
                                        <ConfigInput label="Ruta DB YouTube" name="youtubeDb" category="paths" value={formData.paths.youtubeDb} onChange={handleChange}/>
                                        <ConfigInput label="Ruta DB TikTok" name="tiktokDb" category="paths" value={formData.paths.tiktokDb} onChange={handleChange}/>
                                        <ConfigInput label="Ruta DB Instagram" name="instagramDb" category="paths" value={formData.paths.instagramDb} onChange={handleChange}/>
                                     </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'settings' && (
                        <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                            <h3 className="text-lg font-bold text-white mb-4">Ajustes de Procesamiento</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                                <ConfigInput label="Procesos Concurrentes Máx." type="number" name="maxConcurrentProcessing" category="settings" value={formData.settings.maxConcurrentProcessing} onChange={handleChange} />
                                <ConfigInput label="Tamaño de Miniatura (WxH)" name="thumbnailSize" category="settings" value={formData.settings.thumbnailSize} onChange={handleChange} />
                                
                                <div>
                                  <label className="block text-sm font-medium text-gray-300">Modo de Miniatura</label>
                                  <select name="thumbnailMode" data-category="settings" value={formData.settings.thumbnailMode} onChange={handleChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                                    <option value="ultra_fast">Ultra Rápido</option><option value="balanced">Balanceado</option><option value="quality">Calidad</option><option value="gpu">GPU</option><option value="auto">Auto</option>
                                  </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300">Modelo DeepFace</label>
                                    <select name="deepFaceModel" data-category="settings" value={formData.settings.deepFaceModel} onChange={handleChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none">
                                        <option>VGG-Face</option><option>Facenet</option><option>ArcFace</option><option>OpenFace</option>
                                    </select>
                                </div>
                                
                                <ConfigInput label="Cache DB TTL (segundos)" type="number" name="databaseCacheTTL" category="settings" value={formData.settings.databaseCacheTTL} onChange={handleChange} />
                                <ConfigInput label="Cache DB Tamaño (MB)" type="number" name="databaseCacheSize" category="settings" value={formData.settings.databaseCacheSize} onChange={handleChange} />

                                <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 pt-4 border-t border-gray-700">
                                    <ToggleSwitch label="Usar BD Optimizada" checked={formData.settings.useOptimizedDatabase} onChange={(c) => handleToggleChange('useOptimizedDatabase', 'settings', c)} />
                                    <ToggleSwitch label="Activar Métricas Perf." checked={formData.settings.enablePerformanceMetrics} onChange={(c) => handleToggleChange('enablePerformanceMetrics', 'settings', c)} />
                                    <ToggleSwitch label="Usar GPU para DeepFace" checked={formData.settings.useGPUDeepFace} onChange={(c) => handleToggleChange('useGPUDeepFace', 'settings', c)} />
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end sticky bottom-6">
                        <button type="submit" className="px-8 py-3 bg-red-600 text-white rounded-md hover:bg-red-500 font-semibold shadow-lg">
                            Guardar Cambios
                        </button>
                    </div>
                </form>
            </div>
             <div className="lg:col-span-1 space-y-6 lg:sticky top-6 h-fit">
                <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                    <h3 className="text-lg font-bold text-white mb-4">Resumen de Configuración</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-300">APIs Configuradas</span>
                            <span className="font-bold text-white">{stats.configuredApis} / {totalApis}</span>
                        </div>
                         <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-300">Rutas Válidas</span>
                            <span className="font-bold text-white">{stats.configuredPaths} / {totalPaths}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-300">Perfil</span>
                            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-cyan-500/80 text-cyan-900">Custom</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-300">Última Actualización</span>
                            <span className="text-sm text-gray-400">{new Date().toLocaleDateString()}</span>
                        </div>
                        <div className="pt-4 border-t border-gray-700 flex gap-2">
                             <button className="flex-1 text-sm bg-gray-700 p-2 rounded-md hover:bg-gray-600">Exportar</button>
                             <button className="flex-1 text-sm bg-gray-700 p-2 rounded-md hover:bg-gray-600">Importar</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConfigPage;
