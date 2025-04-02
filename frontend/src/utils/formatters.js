/**
 * Utility functions for data formatting in the CloudSecOps Platform
 */

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

// Configure dayjs
dayjs.extend(relativeTime);

/**
 * Severity level mapping with colors and values
 */
export const SEVERITY_LEVELS = {
  CRITICAL: { value: 'critical', color: '#d32f2f', score: 9 },
  HIGH: { value: 'high', color: '#f44336', score: 7 },
  MEDIUM: { value: 'medium', color: '#ff9800', score: 5 },
  LOW: { value: 'low', color: '#ffeb3b', score: 3 },
  INFO: { value: 'info', color: '#2196f3', score: 1 },
};

/**
 * Format a date string to a human-readable format
 * @param {string} dateString - ISO date string
 * @param {string} format - Output format (default: 'MMM D, YYYY h:mm A')
 * @returns {string} Formatted date string
 */
export const formatDate = (dateString, format = 'MMM D, YYYY h:mm A') => {
  if (!dateString) return 'N/A';
  return dayjs(dateString).format(format);
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 * @param {string} dateString - ISO date string
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'N/A';
  return dayjs(dateString).fromNow();
};

/**
 * Format a number with thousands separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
export const formatNumber = (num) => {
  if (num === undefined || num === null) return 'N/A';
  return num.toLocaleString();
};

/**
 * Format file size in bytes to human-readable format
 * @param {number} bytes - Size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted size string (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  if (!bytes) return 'N/A';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
};

/**
 * Format duration in seconds to human-readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string (e.g., "2h 30m")
 */
export const formatDuration = (seconds) => {
  if (seconds === undefined || seconds === null) return 'N/A';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 && parts.length === 0) parts.push(`${secs}s`);
  
  return parts.join(' ') || '0s';
};

/**
 * Format a percentage value
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value === undefined || value === null) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

/**
 * Get color for a severity level
 * @param {string} severity - Severity level (critical, high, medium, low, info)
 * @returns {string} Color hex code
 */
export const getSeverityColor = (severity) => {
  const level = Object.values(SEVERITY_LEVELS).find(
    level => level.value === severity.toLowerCase()
  );
  return level ? level.color : '#757575'; // Default gray
};

/**
 * Get badge style for a severity level
 * @param {string} severity - Severity level
 * @returns {object} Style object for the badge
 */
export const getSeverityBadgeStyle = (severity) => {
  const color = getSeverityColor(severity);
  return {
    backgroundColor: `${color}20`, // 20% opacity
    color: color,
    borderColor: color,
  };
};

/**
 * Format a cloud provider name for display
 * @param {string} provider - Provider name (aws, azure, etc.)
 * @returns {string} Formatted provider name
 */
export const formatCloudProvider = (provider) => {
  if (!provider) return 'N/A';
  
  const providers = {
    aws: 'AWS',
    azure: 'Azure',
    gcp: 'Google Cloud',
    alibaba: 'Alibaba Cloud',
    oracle: 'Oracle Cloud',
  };
  
  return providers[provider.toLowerCase()] || provider;
};

/**
 * Truncate text with ellipsis if it exceeds max length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};