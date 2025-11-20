import React, { useState } from 'react';
import { Character } from '../../types/admin';
import { ICONS } from '../../constants';

interface CharactersTableProps {
    characters: Character[];
    onEdit: (character: Character) => void;
    onDelete: (id: string) => void;
}

const CharactersTable: React.FC<CharactersTableProps> = ({ characters, onEdit, onDelete }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredCharacters = characters.filter(c => 
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.game.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div>
            <div className="mb-4">
                <input
                    type="text"
                    placeholder="Buscar por nombre o juego..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="w-full max-w-sm bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"
                />
            </div>
            <div className="overflow-x-auto rounded-lg border border-gray-700">
                <table className="w-full text-sm text-left text-gray-300">
                    <thead className="text-xs text-gray-400 uppercase bg-gray-700/50">
                        <tr>
                            <th className="p-4">Nombre</th>
                            <th className="p-4">Juego/Serie</th>
                            <th className="p-4">Prioridad</th>
                            <th className="p-4">Videos</th>
                            <th className="p-4 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {filteredCharacters.map(char => (
                            <tr key={char.id} className="hover:bg-gray-800/50">
                                <td className="p-4 font-semibold text-white">{char.name}</td>
                                <td className="p-4">{char.game}</td>
                                <td className="p-4">{char.priority}</td>
                                <td className="p-4">{char.videoCount}</td>
                                <td className="p-4 text-right">
                                    <div className="flex justify-end items-center gap-4">
                                        <button onClick={() => onEdit(char)} className="text-gray-400 hover:text-white" title="Editar">
                                            {React.cloneElement(ICONS.edit, { className: 'h-5 w-5' })}
                                        </button>
                                        <button onClick={() => onDelete(char.id)} className="text-gray-400 hover:text-red-500" title="Eliminar">
                                            {React.cloneElement(ICONS.delete, { className: 'h-5 w-5' })}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                         {filteredCharacters.length === 0 && (
                            <tr>
                                <td colSpan={5} className="text-center p-8 text-gray-500">No se encontraron personajes.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CharactersTable;
