
import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { Post, EditStatus, Difficulty } from '../types';
import { useData } from '../hooks/useMockData';

interface EditModalProps {
  video?: Post | null; // Renamed to video for less refactoring, but it's a Post
  videoIds?: string[]; // Renamed to videoIds for less refactoring
  onClose: () => void;
}

const EditModal: React.FC<EditModalProps> = ({ video: post, videoIds: postIds = [], onClose }) => {
  const { posts, updatePost, updateMultiplePosts } = useData();
  const [formData, setFormData] = useState({
    editStatus: '',
    difficulty: '',
    music: '',
    artist: '',
    characters: '',
    notes: '',
  });

  const [clearData, setClearData] = useState({
    music: false,
    artist: false,
    characters: false,
    notes: false,
    revertAnalysis: false,
  });

  const isBatchEdit = postIds.length > 0 && !post;
  const targetPost = isBatchEdit ? null : post;

  useEffect(() => {
    if (targetPost) {
      setFormData({
        editStatus: targetPost.editStatus,
        difficulty: targetPost.difficulty,
        music: targetPost.music || '',
        artist: targetPost.artist || '',
        characters: targetPost.characters?.join(', ') || '',
        notes: targetPost.notes || '',
      });
    }
  }, [targetPost]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };
  
  const handleClearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setClearData({...clearData, [e.target.name]: e.target.checked });
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updates: Partial<Post> = {};
    if(formData.editStatus) updates.editStatus = formData.editStatus as EditStatus;
    if(formData.difficulty) updates.difficulty = formData.difficulty as Difficulty;
    if(formData.music) updates.music = formData.music;
    if(formData.artist) updates.artist = formData.artist;
    if(formData.characters) updates.characters = formData.characters.split(',').map(c => c.trim());
    if(formData.notes) updates.notes = formData.notes;

    if(clearData.music) updates.music = undefined;
    if(clearData.artist) updates.artist = undefined;
    if(clearData.characters) updates.characters = undefined;
    if(clearData.notes) updates.notes = undefined;

    if(isBatchEdit) {
        updateMultiplePosts(postIds, updates);
    } else if (post) {
        updatePost(post.id, updates);
    }
    onClose();
  };
  
  const title = isBatchEdit ? `Editar ${postIds.length} Posts` : 'Editar Post';

  return (
    <Modal isOpen={true} onClose={onClose} title={title} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label className="block text-sm font-medium text-gray-300">Estado de Edición</label>
                <select name="editStatus" value={formData.editStatus} onChange={handleChange} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500">
                    <option value="">{isBatchEdit ? 'No cambiar' : 'Seleccionar...'}</option>
                    {Object.values(EditStatus).map(s => <option key={s} value={s}>{s}</option>)}
                </select>
            </div>
             <div>
                <label className="block text-sm font-medium text-gray-300">Dificultad de Edición</label>
                <select name="difficulty" value={formData.difficulty} onChange={handleChange} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500">
                    <option value="">{isBatchEdit ? 'No cambiar' : 'Seleccionar...'}</option>
                    {Object.values(Difficulty).map(d => <option key={d} value={d}>{d}</option>)}
                </select>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-300">Música</label>
                <input type="text" name="music" value={formData.music} onChange={handleChange} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500" />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-300">Artista</label>
                <input type="text" name="artist" value={formData.artist} onChange={handleChange} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500" />
            </div>
            <div className="col-span-1 md:col-span-2">
                <label className="block text-sm font-medium text-gray-300">Personajes (separados por coma)</label>
                <input type="text" name="characters" value={formData.characters} onChange={handleChange} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500" />
            </div>
             <div className="col-span-1 md:col-span-2">
                <label className="block text-sm font-medium text-gray-300">Notas</label>
                <textarea name="notes" value={formData.notes} onChange={handleChange} rows={3} className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm p-2 focus:ring-red-500 focus:border-red-500" />
            </div>
        </div>
        
        {isBatchEdit && (
            <div className="border-t border-gray-700 pt-4">
                 <h3 className="text-md font-medium text-gray-300">Opciones de Limpieza</h3>
                 <div className="grid grid-cols-2 gap-2 mt-2">
                     {Object.keys(clearData).map(key => (
                         <label key={key} className="flex items-center space-x-2">
                             <input type="checkbox" name={key} checked={clearData[key as keyof typeof clearData]} onChange={handleClearChange} className="rounded text-red-600 bg-gray-600 border-gray-500 focus:ring-red-600"/>
                             <span className="text-gray-300">Limpiar {key.replace(/([A-Z])/g, ' $1').toLowerCase()}</span>
                         </label>
                     ))}
                 </div>
            </div>
        )}

        <div className="flex justify-end gap-4 pt-4 border-t border-gray-700">
          <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500">
            Cancelar
          </button>
          <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500">
            Aplicar Cambios
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EditModal;
