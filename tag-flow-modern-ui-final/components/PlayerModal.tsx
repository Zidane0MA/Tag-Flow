
import React from 'react';
import Modal from './Modal';
import { Post, Difficulty } from '../types';
import { useRealData } from '../hooks/useRealData';
import { ICONS } from '../constants';

interface PlayerModalProps {
  video: Post;
  onClose: () => void;
}

const PlayerModal: React.FC<PlayerModalProps> = ({ video: post, onClose }) => {
  const { updatePost, moveToTrash } = useRealData();

  const handleDifficultyChange = (newDifficulty: Difficulty) => {
    updatePost(post.id, { difficulty: newDifficulty });
  };
  
  const handleDelete = () => {
    moveToTrash(post.id);
    onClose();
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Reproductor de Video" size="xl">
      <div className="flex flex-col md:flex-row gap-6">
        <div className="flex-grow md:w-2/3 bg-black rounded-lg overflow-hidden">
           <video src={post.postUrl} controls autoPlay className="w-full h-full object-contain"></video>
        </div>
        <div className="md:w-1/3 flex flex-col gap-4">
          <div>
            <h3 className="text-xl font-bold text-white">{post.title}</h3>
            <p className="text-sm text-red-500">por {post.creator}</p>
          </div>
          <p className="text-sm text-gray-300">{post.description}</p>
          <div className="text-sm space-y-2 text-gray-400">
            {post.music && <p><strong>Música:</strong> {post.music}</p>}
            {post.characters && <p><strong>Personajes:</strong> {post.characters.join(', ')}</p>}
            <p><strong>Plataforma:</strong> {post.platform}</p>
            <p><strong>Descargado:</strong> {new Date(post.downloadDate).toLocaleString()}</p>
            <p><strong>Duración:</strong> {Math.floor(post.duration / 60)}m {post.duration % 60}s</p>
          </div>
          <div className="mt-auto pt-4 border-t border-gray-700">
             <div className="mb-4">
                <span className="text-sm font-medium text-gray-300 mr-2">Dificultad Edición:</span>
                <div className="inline-flex rounded-md shadow-sm" role="group">
                    {Object.values(Difficulty).map(d => (
                         <button
                            key={d}
                            onClick={() => handleDifficultyChange(d)}
                            className={`px-3 py-1 text-sm font-medium border border-gray-600 transition-colors first:rounded-l-lg last:rounded-r-lg ${post.difficulty === d ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
                         >
                             {d}
                         </button>
                    ))}
                </div>
             </div>
             <div className="flex gap-2">
                 <button className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-500 transition-colors flex items-center justify-center gap-2" onClick={handleDelete}>
                    {ICONS.delete} Eliminar
                 </button>
             </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default PlayerModal;
