import React, { useRef, useEffect, useState } from 'react';
import styles from './ManuscriptViewer.module.css';

interface Selection {
  start: number;
  end: number;
  text: string;
}

interface ManuscriptViewerProps {
  content: string;
  onTextSelection: (start: number, end: number, text: string) => void;
  selection: Selection | null;
}

const ManuscriptViewer: React.FC<ManuscriptViewerProps> = ({
  content,
  onTextSelection,
  selection,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [isSelecting, setIsSelecting] = useState(false);

  useEffect(() => {
    const handleMouseUp = () => {
      if (!contentRef.current) return;

      const windowSelection = window.getSelection();
      if (!windowSelection || windowSelection.rangeCount === 0) return;

      const range = windowSelection.getRangeAt(0);
      const selectedText = range.toString().trim();

      if (selectedText.length === 0) return;

      // Simple approach: find the selected text in the content string
      const contentText = content;
      const startIndex = contentText.indexOf(selectedText);

      if (startIndex !== -1) {
        const endIndex = startIndex + selectedText.length;
        onTextSelection(startIndex, endIndex, selectedText);
      }

      setIsSelecting(false);
    };

    const handleMouseDown = () => {
      setIsSelecting(true);
    };

    const element = contentRef.current;
    if (element) {
      element.addEventListener('mouseup', handleMouseUp);
      element.addEventListener('mousedown', handleMouseDown);
    }

    return () => {
      if (element) {
        element.removeEventListener('mouseup', handleMouseUp);
        element.removeEventListener('mousedown', handleMouseDown);
      }
    };
  }, [onTextSelection, content]);

  // Render content - keep it simple to avoid DOM corruption
  const renderContent = () => {
    return formatContent(content);
  };

  // Simple markdown-like formatting
  const formatContent = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, index) => {
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className={styles.heading1}>
            {line.substring(2)}
          </h1>
        );
      } else if (line.startsWith('## ')) {
        return (
          <h2 key={index} className={styles.heading2}>
            {line.substring(3)}
          </h2>
        );
      } else if (line.startsWith('### ')) {
        return (
          <h3 key={index} className={styles.heading3}>
            {line.substring(4)}
          </h3>
        );
      } else if (line.trim() === '') {
        return <br key={index} />;
      } else {
        return (
          <p key={index} className={styles.paragraph}>
            {line}
          </p>
        );
      }
    });
  };

  return (
    <div className={styles.viewer}>
      <div className={styles.content} ref={contentRef}>
        {renderContent()}
      </div>
      
      {selection && (
        <div className={styles.selectionInfo}>
          <div className={styles.selectionStats}>
            Selected: {selection.text.length} characters ({selection.start}-{selection.end})
          </div>
        </div>
      )}
    </div>
  );
};

export default ManuscriptViewer;
