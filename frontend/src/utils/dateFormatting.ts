/**
 * German date and time formatting utilities
 * All dates will be displayed in German format (DD.MM.YYYY HH:mm:ss)
 */

/**
 * Format a date string to German format
 * @param dateString - ISO date string, Date object, or null/undefined
 * @returns Formatted German date string (DD.MM.YYYY HH:mm:ss) or 'N/A'
 */
export const formatGermanDate = (dateString: string | Date | null | undefined): string => {
  if (dateString == null) return 'N/A';
  const date = new Date(dateString);
  
  // Check if date is valid (reject epoch 0 which often indicates null)
  if (isNaN(date.getTime()) || date.getTime() === 0) {
    return 'N/A';
  }
  
  // Format to German format: DD.MM.YYYY HH:mm:ss
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');
  
  return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
};

/**
 * Format a date string to German date only (DD.MM.YYYY)
 * @param dateString - ISO date string or Date object
 * @returns Formatted German date string (DD.MM.YYYY)
 */
export const formatGermanDateOnly = (dateString: string | Date): string => {
  const date = new Date(dateString);
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return 'Ungültiges Datum';
  }
  
  // Format to German date format: DD.MM.YYYY
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  
  return `${day}.${month}.${year}`;
};

/**
 * Format a date string to German time only (HH:mm:ss)
 * @param dateString - ISO date string or Date object
 * @returns Formatted German time string (HH:mm:ss)
 */
export const formatGermanTimeOnly = (dateString: string | Date): string => {
  const date = new Date(dateString);
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return 'Ungültige Zeit';
  }
  
  // Format to German time format: HH:mm:ss
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');
  
  return `${hours}:${minutes}:${seconds}`;
};

/**
 * Format a date string to German relative time (e.g., "vor 2 Stunden")
 * @param dateString - ISO date string or Date object
 * @returns Formatted German relative time string
 */
export const formatGermanRelativeTime = (dateString: string | Date): string => {
  const date = new Date(dateString);
  const now = new Date();
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    return 'Ungültiges Datum';
  }
  
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) {
    return 'vor einem Moment';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `vor ${minutes} Minute${minutes !== 1 ? 'n' : ''}`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `vor ${hours} Stunde${hours !== 1 ? 'n' : ''}`;
  } else if (diffInSeconds < 2592000) {
    const days = Math.floor(diffInSeconds / 86400);
    return `vor ${days} Tag${days !== 1 ? 'en' : ''}`;
  } else {
    // For older dates, show the actual date
    return formatGermanDate(date);
  }
};
