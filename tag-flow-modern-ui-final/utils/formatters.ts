export const formatDuration = (seconds: number): string => {
  if (isNaN(seconds) || seconds < 0) {
    return '00:00';
  }

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  const pad = (num: number): string => num.toString().padStart(2, '0');

  if (hours > 0) {
    return `${hours}:${pad(minutes)}:${pad(remainingSeconds)}`;
  } else {
    return `${minutes}:${pad(remainingSeconds)}`;
  }
};

export const formatFileSize = (mb: number): string => {
  if (isNaN(mb) || mb < 0) {
    return '0 MB';
  }

  const bytes = mb * 1024 * 1024; // Convert MB to bytes

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let size = bytes;

  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }

  return `${size.toFixed(1)} ${units[i]}`;
};
