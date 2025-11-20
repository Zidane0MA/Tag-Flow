import React from 'react';

interface PaginationProps {
    currentPage: number;
    totalItems: number;
    itemsPerPage: number;
    onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalItems, itemsPerPage, onPageChange }) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    if (totalPages <= 1) {
        return null;
    }

    const handlePageClick = (page: number) => {
        if (page >= 1 && page <= totalPages) {
            onPageChange(page);
        }
    };
    
    const pageNumbers = [];
    const maxPagesToShow = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

    if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
    }

    return (
        <div className="flex justify-center items-center mt-8">
            <button
                onClick={() => handlePageClick(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 mx-1 text-gray-300 bg-gray-800 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
            >
                Anterior
            </button>
            
            {startPage > 1 && (
                <>
                    <button onClick={() => handlePageClick(1)} className="px-4 py-2 mx-1 text-gray-300 bg-gray-800 rounded-md hover:bg-gray-700">1</button>
                    {startPage > 2 && <span className="px-4 py-2 mx-1 text-gray-500">...</span>}
                </>
            )}

            {pageNumbers.map(number => (
                <button
                    key={number}
                    onClick={() => handlePageClick(number)}
                    className={`px-4 py-2 mx-1 rounded-md ${
                        currentPage === number
                            ? 'bg-red-600 text-white font-bold'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                >
                    {number}
                </button>
            ))}

            {endPage < totalPages && (
                 <>
                    {endPage < totalPages -1 && <span className="px-4 py-2 mx-1 text-gray-500">...</span>}
                    <button onClick={() => handlePageClick(totalPages)} className="px-4 py-2 mx-1 text-gray-300 bg-gray-800 rounded-md hover:bg-gray-700">{totalPages}</button>
                </>
            )}

            <button
                onClick={() => handlePageClick(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 mx-1 text-gray-300 bg-gray-800 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700"
            >
                Siguiente
            </button>
        </div>
    );
};

export default Pagination;