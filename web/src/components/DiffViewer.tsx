import React from 'react';
import styles from './DiffViewer.module.css';

interface DiffViewerProps {
  before: string;
  after: string;
  isExpanded: boolean;
  onToggle: () => void;
}

const DiffViewer: React.FC<DiffViewerProps> = ({
  before,
  after,
  isExpanded,
  onToggle,
}) => {
  // Simple diff computation for display
  const computeSimpleDiff = (oldText: string, newText: string) => {
    // For now, just show the full before/after
    // In a production app, you'd use a proper diff algorithm
    return {
      removed: oldText !== newText ? oldText : '',
      added: oldText !== newText ? newText : oldText,
    };
  };

  const diff = computeSimpleDiff(before, after);
  const hasChanges = before !== after;

  const previewLength = 100;
  const preview = after.length > previewLength 
    ? `${after.substring(0, previewLength)}...` 
    : after;

  return (
    <div className={styles.diffViewer}>
      <div className={styles.preview} onClick={onToggle}>
        <div className={styles.previewText}>
          {preview}
        </div>
        <div className={styles.toggleButton}>
          {isExpanded ? '▼ Hide diff' : '▶ Show diff'}
        </div>
      </div>

      {isExpanded && (
        <div className={styles.fullDiff}>
          {hasChanges ? (
            <div className={styles.sideBySide}>
              <div className={styles.beforeColumn}>
                <div className={styles.columnHeader}>Before</div>
                <div className={styles.diffContent}>
                  <div className={styles.removedText}>
                    {diff.removed}
                  </div>
                </div>
              </div>
              
              <div className={styles.afterColumn}>
                <div className={styles.columnHeader}>After</div>
                <div className={styles.diffContent}>
                  <div className={styles.addedText}>
                    {diff.added}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className={styles.noChanges}>
              No changes detected
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DiffViewer;
