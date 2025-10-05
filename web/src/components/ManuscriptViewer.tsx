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
      const selectedText = range.toString();

      if (selectedText.trim().length === 0) return;

      // Get the position of the selection within the content
      try {
        // Create a range from the start of the content to the start of the selection
        const preRange = document.createRange();
        preRange.selectNodeContents(contentRef.current);
        preRange.setEnd(range.startContainer, range.startOffset);

        // Get the text before the selection to calculate the start position
        const textBeforeSelection = preRange.toString();
        const startIndex = textBeforeSelection.length;
        const endIndex = startIndex + selectedText.length;

        console.log('Selection details:', {
          selectedText: selectedText.substring(0, 100) + (selectedText.length > 100 ? '...' : ''),
          selectedLength: selectedText.length,
          startIndex,
          endIndex,
          contentLength: content.length
        });

        // Validate that the indices are within bounds
        if (startIndex >= 0 && endIndex <= content.length && startIndex < endIndex) {
          onTextSelection(startIndex, endIndex, selectedText);
        } else {
          console.warn('Selection indices out of bounds, trying fallback');
          // Fallback to simple indexOf approach
          const trimmedText = selectedText.trim();
          const fallbackStart = content.indexOf(trimmedText);
          if (fallbackStart !== -1) {
            const fallbackEnd = fallbackStart + trimmedText.length;
            onTextSelection(fallbackStart, fallbackEnd, trimmedText);
          }
        }
      } catch (error) {
        console.error('Selection error:', error);
        // Fallback to simple indexOf approach
        const trimmedText = selectedText.trim();
        const startIndex = content.indexOf(trimmedText);
        if (startIndex !== -1) {
          const endIndex = startIndex + trimmedText.length;
          onTextSelection(startIndex, endIndex, trimmedText);
        }
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
