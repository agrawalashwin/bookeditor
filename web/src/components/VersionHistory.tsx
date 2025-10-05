import React, { useState, useEffect } from 'react';
import { manuscriptApi } from '../lib/api';
import styles from './VersionHistory.module.css';

interface Version {
  id: string;
  version_tag: string;
  created_at: string;
  is_current: boolean;
}

interface VersionHistoryProps {
  manuscriptId: string;
  onClose: () => void;
  onRevert: (versionId: string) => void;
}

const VersionHistory: React.FC<VersionHistoryProps> = ({ manuscriptId, onClose, onRevert }) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [manuscriptId]);

  const loadHistory = async () => {
    try {
      const history = await manuscriptApi.getHistory(manuscriptId);
      setVersions(history.versions || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = (version: Version) => {
    if (version.is_current) {
      alert('This is already the current version.');
      return;
    }

    const confirmed = window.confirm(
      `Revert to version: ${version.version_tag}?\n\n` +
      `Created: ${new Date(version.created_at).toLocaleString()}\n\n` +
      `This will restore the manuscript to this version.`
    );

    if (confirmed) {
      onRevert(version.id);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Version History</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>

        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>Loading history...</div>
          ) : versions.length === 0 ? (
            <div className={styles.empty}>No version history available.</div>
          ) : (
            <div className={styles.versionList}>
              {versions.map((version, index) => (
                <div 
                  key={version.id} 
                  className={`${styles.versionItem} ${version.is_current ? styles.current : ''}`}
                >
                  <div className={styles.versionInfo}>
                    <div className={styles.versionTag}>
                      {version.version_tag}
                      {version.is_current && <span className={styles.badge}>Current</span>}
                      {index === 0 && !version.is_current && <span className={styles.badge}>Latest</span>}
                    </div>
                    <div className={styles.versionDate}>
                      {formatDate(version.created_at)}
                    </div>
                  </div>
                  {!version.is_current && (
                    <button 
                      className={styles.revertButton}
                      onClick={() => handleRevert(version)}
                    >
                      Restore
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className={styles.footer}>
          <p className={styles.hint}>
            💡 Tip: You can restore any previous version of your manuscript
          </p>
        </div>
      </div>
    </div>
  );
};

export default VersionHistory;
