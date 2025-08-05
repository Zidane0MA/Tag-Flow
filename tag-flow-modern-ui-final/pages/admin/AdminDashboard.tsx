
import React from 'react';
import { Link } from 'react-router-dom';
import { useAdminData } from '../../hooks/useAdminData';
import StatCard from '../../components/StatCard';
import { ICONS } from '../../constants';
import { Operation, OperationStatus, OperationType } from '../../types/admin';

const NavCard: React.FC<{ to: string, icon: React.ReactElement<any>, title: string, description: string, badge?: string | number | null }> = ({ to, icon, title, description, badge }) => (
    <Link to={to} className="bg-[#212121] p-6 rounded-lg shadow-lg hover:bg-gray-800/60 transition-all duration-300 flex items-start gap-4 hover:-translate-y-1 group">
        <div className="text-red-500">{React.cloneElement(icon, { className: 'h-8 w-8' })}</div>
        <div className="flex-1">
            <h3 className="font-bold text-white text-lg flex items-center gap-2">{title} 
                {badge != null && <span className="text-xs bg-red-600 px-2 py-0.5 rounded-full">{badge}</span>}
            </h3>
            <p className="text-sm text-gray-400 mt-1">{description}</p>
        </div>
        <div className="text-gray-600 group-hover:text-red-500 transition-colors">
            {React.cloneElement(ICONS.chevronRight, { className: 'h-6 w-6' })}
        </div>
    </Link>
);

const OperationStatusIcon = ({ status }: { status: OperationStatus }) => {
    const iconMap = {
        [OperationStatus.COMPLETED]: <span className="text-green-500">{ICONS.status_completed}</span>,
        [OperationStatus.RUNNING]: <span className="text-blue-500 animate-spin">{ICONS.spinner}</span>,
        [OperationStatus.FAILED]: <span className="text-red-500">{ICONS.close}</span>,
        [OperationStatus.CANCELLED]: <span className="text-yellow-500">{ICONS.status_pending}</span>,
        [OperationStatus.PENDING]: <span className="text-gray-500">{ICONS.clock}</span>
    };
    return iconMap[status] || null;
};

const RecentActivityItem: React.FC<{ op: Operation }> = ({ op }) => (
    <div className="flex items-center gap-4 py-3">
        <div><OperationStatusIcon status={op.status} /></div>
        <div className="flex-1">
            <p className="font-semibold text-gray-200">{op.type}</p>
            <p className="text-xs text-gray-500">{op.message}</p>
        </div>
        <div className="text-sm text-gray-400">{new Date(op.startTime).toLocaleTimeString()}</div>
    </div>
);


const AdminDashboard: React.FC = () => {
    const { stats, operations, startOperation } = useAdminData();
    const diskUsagePercent = ((stats.diskUsage / stats.diskTotal) * 100).toFixed(1);
    const totalApis = 7; // youtube, spotify id/secret, google, acrcloud host/key/secret

    const quickActions = [
        { name: 'Procesar Videos', type: OperationType.PROCESS_VIDEOS, icon: ICONS.play },
        { name: 'Crear Backup', type: OperationType.BACKUP, icon: ICONS.database },
        { name: 'Verificar Sistema', type: OperationType.VERIFY_SYSTEM, icon: ICONS.hardDrive },
        { name: 'Optimizar BD', type: OperationType.OPTIMIZE_DB, icon: ICONS.bolt },
    ];

    return (
        <div className="space-y-8">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Posts Totales" value={stats.totalPosts} icon={ICONS.gallery} />
                <StatCard title="Operaciones Activas" value={stats.activeOperations} icon={ICONS.terminal} />
                <StatCard title="Videos Pendientes" value={stats.pendingVideos} icon={ICONS.status_pending} />
                <StatCard title="Uso de Disco" value={`${diskUsagePercent}%`} icon={ICONS.hardDrive} />
            </div>

            {/* Navigation Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <NavCard to="/admin/operations" icon={ICONS.terminal} title="Operaciones" description="Procesar videos, análisis y operaciones en tiempo real." badge={stats.activeOperations > 0 ? stats.activeOperations : null} />
                <NavCard to="/admin/config" icon={ICONS.wrench} title="Configuración" description="APIs, rutas y configuración del sistema." badge={`${stats.configuredApis}/${totalApis} APIs`} />
                <NavCard to="/admin/characters" icon={ICONS.users} title="Personajes" description="Gestión de personajes y detección de caracteres." badge={stats.totalCharacters} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Recent Activity */}
                <div className="lg:col-span-2 bg-[#212121] p-6 rounded-lg shadow-lg">
                    <h3 className="font-bold text-white text-lg mb-4">Actividad Reciente</h3>
                    <div className="space-y-2 divide-y divide-gray-700/50">
                        {operations.slice(0, 5).map(op => <RecentActivityItem key={op.id} op={op} />)}
                        {operations.length === 0 && <p className="text-gray-500 text-center py-4">No hay actividad reciente.</p>}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-[#212121] p-6 rounded-lg shadow-lg">
                    <h3 className="font-bold text-white text-lg mb-4">Acciones Rápidas</h3>
                    <div className="grid grid-cols-2 gap-3">
                        {quickActions.map(action => (
                            <button key={action.name} onClick={() => startOperation(action.type)} className="bg-gray-700 text-gray-200 hover:bg-red-600 hover:text-white p-3 rounded-md flex flex-col items-center justify-center gap-2 transition-colors text-sm font-semibold">
                                {React.cloneElement(action.icon, { className: "h-6 w-6"})}
                                <span>{action.name}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
