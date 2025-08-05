import React, { useState, useEffect } from 'react';
import Modal from '../Modal';
import { Character } from '../../types/admin';

interface CharacterModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (character: Character) => void;
    character: Character | null;
    games: string[];
}

const emptyCharacterState = {
    name: '',
    game: '',
    variants: { exact: [], joined: [], native: [], common: [] },
    contextHints: [],
    detectionWeight: 0.8,
    priority: 3,
};

const toTextArea = (arr: string[] = []) => arr.join(', ');
const fromTextArea = (str: string = '') => str.split(',').map(s => s.trim()).filter(Boolean);

const CharacterModal: React.FC<CharacterModalProps> = ({ isOpen, onClose, onSave, character, games }) => {
    const [formData, setFormData] = useState(emptyCharacterState);

    useEffect(() => {
        if (character) {
            setFormData(character);
        } else {
            setFormData(emptyCharacterState);
        }
    }, [character]);

    const handleTextChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: parseFloat(value) }));
    };

    const handleVariantsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ 
            ...prev, 
            variants: {
                ...prev.variants,
                [name]: fromTextArea(value)
            }
        }));
    };
    
    const handleHintsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setFormData(prev => ({ ...prev, contextHints: fromTextArea(e.target.value)}));
    };

    const handleSave = () => {
        // The state `formData` already matches the structure of `Omit<Character, 'id' | 'videoCount'>`.
        // We cast it to Character for the onSave prop.
        onSave(formData as Character);
    };
    
    const title = character ? 'Editar Personaje' : 'Añadir Personaje';

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={title} size="lg">
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">Nombre Canónico</label>
                        <input type="text" name="name" value={formData.name} onChange={handleTextChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300">Juego/Serie</label>
                        <input type="text" name="game" list="games" value={formData.game} onChange={handleTextChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"/>
                        <datalist id="games">
                            {games.map(g => <option key={g} value={g} />)}
                        </datalist>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                     <div>
                        <label className="block text-sm font-medium text-gray-300">Prioridad (1-5)</label>
                        <input type="number" name="priority" min="1" max="5" value={formData.priority} onChange={handleNumberChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300">Peso Detección (0-1)</label>
                        <input type="number" name="detectionWeight" min="0" max="1" step="0.05" value={formData.detectionWeight} onChange={handleNumberChange} className="mt-1 w-full bg-gray-700 text-white rounded p-2 focus:ring-2 focus:ring-red-500 focus:outline-none"/>
                    </div>
                </div>
                
                <div className="space-y-3 pt-2">
                    <h4 className="text-md font-semibold text-gray-200">Variantes y Alias (separados por comas)</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                             <label className="block text-sm font-medium text-gray-400">Exactos</label>
                             <textarea name="exact" value={toTextArea(formData.variants.exact)} onChange={handleVariantsChange} rows={2} className="mt-1 w-full bg-gray-700 text-white rounded p-2 text-sm"/>
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-400">Unidos (camelCase)</label>
                             <textarea name="joined" value={toTextArea(formData.variants.joined)} onChange={handleVariantsChange} rows={2} className="mt-1 w-full bg-gray-700 text-white rounded p-2 text-sm"/>
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-400">Nativos (Japonés, etc.)</label>
                             <textarea name="native" value={toTextArea(formData.variants.native)} onChange={handleVariantsChange} rows={2} className="mt-1 w-full bg-gray-700 text-white rounded p-2 text-sm"/>
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-400">Alias Comunes</label>
                             <textarea name="common" value={toTextArea(formData.variants.common)} onChange={handleVariantsChange} rows={2} className="mt-1 w-full bg-gray-700 text-white rounded p-2 text-sm"/>
                        </div>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300">Pistas de Contexto (separadas por comas)</label>
                    <textarea name="contextHints" value={toTextArea(formData.contextHints)} onChange={handleHintsChange} rows={2} className="mt-1 w-full bg-gray-700 text-white rounded p-2"/>
                </div>

                 <div className="pt-4 flex justify-end gap-3 border-t border-gray-700">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500">Cancelar</button>
                    <button onClick={handleSave} className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500">Guardar</button>
                </div>
            </div>
        </Modal>
    );
};

export default CharacterModal;
