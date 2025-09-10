export const formatTimeAgo = (timeString: string) => {
  try {
    let time: Date;
    // Check if timeString is a number (Unix timestamp)
    if (!isNaN(Number(timeString)) && !isNaN(parseFloat(timeString))) {
      time = new Date(Number(timeString) * 1000); // Convert seconds to milliseconds
    } else {
      time = new Date(timeString);
    }

    if (isNaN(time.getTime())) {
      return 'Unknown time';
    }

    const diff = new Date().getTime() - time.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  } catch (error) {
    return 'Unknown time';
  }
};
