import React, { useState } from 'react';
import { useAdminData } from '../../hooks/useAdminData';
import StatCard from '../../components/StatCard';
import { ICONS } from '../../constants';
import CharactersTable from '../../components/admin/CharactersTable';
import CharacterModal from '../../components/admin/CharacterModal';
import { Character, OperationType } from '../../types/admin';

const Section: React.FC<{ title: string, children: React.ReactNode, className?: string }> = ({ title, children, className }) => (
    <div className={`bg-[#212121] p-6 rounded-lg shadow-lg ${className}`}>
        <h3 className="font-bold text-white text-lg mb-4">{title}</h3>
        {children}
    </div>
);

const GamesManagement: React.FC = () => {
    const { games, addGame } = useAdminData();
    const [newGame, setNewGame] = useState('');

    const handleAddGame = () => {
        addGame(newGame);
        setNewGame('');
    };

    return (
        <Section title="Gestión de Juegos/Series">
            <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                {games.map(game => (
                    <div key={game} className="flex justify-between items-center bg-gray-800/50 p-2 rounded-md text-sm">
                        <span className="font-medium">{game}</span>
                        <button className="text-xs text-gray-400 hover:text-white">Renombrar</button>
                    </div>
                ))}
            </div>
            <div className="flex gap-2 mt-4 pt-4 border-t border-gray-700">
                <input 
                    type="text" 
                    value={newGame}
                    onChange={e => setNewGame(e.target.value)}
                    placeholder="Nuevo nombre de juego"
                    className="flex-grow w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none text-sm"
                />
                <button onClick={handleAddGame} className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500 font-semibold text-sm">Añadir</button>
            </div>
        </Section>
    );
};

const CharacterStats: React.FC = () => {
    const { stats } = useAdminData();
    // Mock data for charts
    const topCharacters = [{name: 'Gawr Gura', detections: 15}, {name: 'Hatsune Miku', detections: 22}, {name: 'Zhongli', detections: 8}].sort((a,b) => b.detections - a.detections);
    const gameDistribution = [{game: 'Hololive', count: 1}, {game: 'Vocaloid', count: 1}, {game: 'Genshin Impact', count: 1}];
    const maxDetections = Math.max(...topCharacters.map(c => c.detections));

    return (
        <Section title="Estadísticas de Personajes">
            <div className="space-y-4">
                <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-2">Top Personajes Detectados</h4>
                    <div className="space-y-2">
                        {topCharacters.map(c => (
                            <div key={c.name} className="flex items-center gap-2 text-xs">
                                <span className="w-24 truncate font-medium" title={c.name}>{c.name}</span>
                                <div className="flex-1 bg-gray-700 rounded-full h-4">
                                    <div className="bg-red-500 h-4 rounded-full text-right pr-2 text-white" style={{width: `${(c.detections/maxDetections)*100}%`}}>{c.detections}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                 <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-2">Distribución por Juego</h4>
                    <div className="flex gap-2 h-24 items-end">
                       {gameDistribution.map(g => (
                           <div key={g.game} className="flex-1 flex flex-col items-center justify-end text-center group">
                                <div className="w-full bg-cyan-500 group-hover:bg-cyan-400 transition-all" style={{height: `${(g.count / stats.totalGames) * 80 + 20}%`}}></div>
                                <span className="text-xs mt-1 truncate">{g.game}</span>
                           </div>
                       ))}
                    </div>
                </div>
            </div>
        </Section>
    );
}


const CharactersPage: React.FC = () => {
    const { stats, characters, games, addCharacter, updateCharacter, deleteCharacter, startOperation } = useAdminData();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);

    const handleOpenAddModal = () => {
        setEditingCharacter(null);
        setIsModalOpen(true);
    };

    const handleOpenEditModal = (character: Character) => {
        setEditingCharacter(character);
        setIsModalOpen(true);
    };
    
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setEditingCharacter(null);
    };

    const handleSaveCharacter = (characterData: Character) => {
        if(editingCharacter) {
            updateCharacter(characterData);
        } else {
            addCharacter(characterData as Omit<Character, 'id' | 'videoCount'>);
        }
        handleCloseModal();
    }


    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Personajes" value={stats.totalCharacters} icon={ICONS.users} />
                <StatCard title="Juegos/Series" value={stats.totalGames} icon={ICONS.reels} />
                <StatCard title="Precisión Detección" value="92.1%" icon={ICONS.analyze} />
                <StatCard title="Videos con Personajes" value={stats.withCharacters} icon={ICONS.gallery} />
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    <Section title="Gestión de Personajes">
                        <div className="flex justify-end items-center mb-4">
                            <button onClick={handleOpenAddModal} className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500 font-semibold transition-colors">
                                {ICONS.plus}
                                Añadir Personaje
                            </button>
                        </div>
                        <CharactersTable 
                            characters={characters}
                            onEdit={handleOpenEditModal}
                            onDelete={deleteCharacter}
                        />
                    </Section>
                </div>
                <div className="lg:col-span-1 space-y-8">
                    <GamesManagement />
                    <CharacterStats />
                </div>
            </div>

            <Section title="Operaciones de Personajes">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <button onClick={() => startOperation(OperationType.CLEAN_FALSE_POSITIVES)} className="p-3 bg-gray-700 rounded-md hover:bg-red-600 text-sm font-semibold transition">Limpiar Falsos Positivos</button>
                    <button onClick={() => startOperation(OperationType.UPDATE_CREATOR_MAPPINGS)} className="p-3 bg-gray-700 rounded-md hover:bg-red-600 text-sm font-semibold transition">Actualizar Mapeos</button>
                    <button onClick={() => startOperation(OperationType.ANALYZE_TITLES, {limit: 500})} className="p-3 bg-gray-700 rounded-md hover:bg-red-600 text-sm font-semibold transition">Analizar Títulos</button>
                    <button onClick={() => startOperation(OperationType.DOWNLOAD_CHARACTER_IMAGES)} className="p-3 bg-gray-700 rounded-md hover:bg-red-600 text-sm font-semibold transition">Descargar Imágenes</button>
                </div>
            </Section>

            {isModalOpen && (
                 <CharacterModal
                    isOpen={isModalOpen}
                    onClose={handleCloseModal}
                    onSave={handleSaveCharacter}
                    character={editingCharacter}
                    games={games}
                />
            )}
        </div>
    );
};

export default CharactersPage;
