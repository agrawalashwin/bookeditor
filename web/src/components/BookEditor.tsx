import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { manuscriptApi, editApi, EditOption } from '../lib/api';
import ManuscriptViewer from './ManuscriptViewer';
import EditConsole from './EditConsole';
import VersionHistory from './VersionHistory';
import styles from './BookEditor.module.css';

interface Selection {
  start: number;
  end: number;
  text: string;
}

const BookEditor: React.FC = () => {
  const [manuscriptId, setManuscriptId] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [editSessionId, setEditSessionId] = useState<string | null>(null);
  const [editOptions, setEditOptions] = useState<EditOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const queryClient = useQueryClient();

  // Load or create manuscript
  useEffect(() => {
    // Always try to load the latest manuscript from upload script first
    fetch('/current_manuscript_id.txt')
      .then(response => response.text())
      .then(id => {
        if (id.trim()) {
          const newId = id.trim();
          setManuscriptId(newId);
          localStorage.setItem('currentManuscriptId', newId);
        } else {
          // Fallback to saved ID
          const savedManuscriptId = localStorage.getItem('currentManuscriptId');
          if (savedManuscriptId) {
            setManuscriptId(savedManuscriptId);
          } else {
            createDemoManuscript();
          }
        }
      })
      .catch(() => {
        // Fallback to saved ID
        const savedManuscriptId = localStorage.getItem('currentManuscriptId');
        if (savedManuscriptId) {
          setManuscriptId(savedManuscriptId);
        } else {
          createDemoManuscript();
        }
      });
  }, []);

  const createDemoManuscript = async () => {
    try {
      const demoContent = `# The Great Adventure

## Chapter 1: The Beginning

It was a dark and stormy night when Sarah first discovered the mysterious letter hidden beneath the floorboards of her grandmother's attic. The parchment was yellowed with age, and the ink had faded to a rusty brown, but the words were still legible.

"My dearest Sarah," it began, "if you are reading this, then the time has come for you to learn the truth about our family's greatest secret."

Sarah's hands trembled as she continued reading. The letter spoke of hidden treasures, ancient curses, and a quest that had been passed down through generations of her family. Each word seemed to pull her deeper into a world she never knew existed.

## Chapter 2: The Discovery

The next morning, Sarah couldn't shake the feeling that her life had changed forever. She sat at her kitchen table, the letter spread out before her, trying to make sense of what she had read. The handwriting was definitely her grandmother's, but the story it told seemed impossible.

According to the letter, their family had been guardians of a powerful artifact for over two centuries. The artifact, known as the Moonstone of Eldara, was said to possess the ability to reveal hidden truths and unlock doors to other realms.

Sarah had always thought her grandmother's stories were just fairy tales, but now she wasn't so sure.`;

      const manuscript = await manuscriptApi.create({
        title: 'The Great Adventure',
        author: 'Demo Author',
        content: demoContent
      });
      
      setManuscriptId(manuscript.id);
      localStorage.setItem('currentManuscriptId', manuscript.id);
    } catch (error) {
      console.error('Failed to create demo manuscript:', error);
    }
  };

  // Fetch manuscript content
  const { data: manuscriptContent, refetch: refetchContent } = useQuery({
    queryKey: ['manuscript-content', manuscriptId],
    queryFn: () => manuscriptId ? manuscriptApi.getContent(manuscriptId) : null,
    enabled: !!manuscriptId,
  });

  // Fetch manuscript metadata
  const { data: manuscript } = useQuery({
    queryKey: ['manuscript', manuscriptId],
    queryFn: () => manuscriptId ? manuscriptApi.get(manuscriptId) : null,
    enabled: !!manuscriptId,
  });

  // Suggest edits mutation
  const suggestEditsMutation = useMutation({
    mutationFn: editApi.suggest,
    onSuccess: (data) => {
      setEditSessionId(data.edit_session_id);
      setEditOptions(data.options);
      setIsLoading(false);
    },
    onError: (error) => {
      console.error('Failed to get edit suggestions:', error);
      setIsLoading(false);
    },
  });

  // Apply edit mutation
  const applyEditMutation = useMutation({
    mutationFn: editApi.apply,
    onSuccess: () => {
      // Refresh manuscript content
      refetchContent();
      // Clear edit session
      setEditSessionId(null);
      setEditOptions([]);
      setSelection(null);
      queryClient.invalidateQueries({ queryKey: ['manuscript', manuscriptId] });
    },
    onError: (error) => {
      console.error('Failed to apply edit:', error);
    },
  });

  const handleTextSelection = (start: number, end: number, text: string) => {
    // Validate the selection to prevent corruption
    if (start >= 0 && end > start && text.length > 0 && manuscriptContent?.content) {
      // Double-check that the selected text matches what's in the content
      const actualText = manuscriptContent.content.substring(start, end);
      if (actualText === text) {
        setSelection({ start, end, text });
        // Clear previous edit session
        setEditSessionId(null);
        setEditOptions([]);
      } else {
        console.warn('Text selection mismatch, ignoring selection');
      }
    }
  };

  const handleSuggestEdits = async (instruction: string) => {
    if (!selection || !manuscriptId) return;

    setIsLoading(true);
    suggestEditsMutation.mutate({
      manuscript_id: manuscriptId,
      instruction,
      target_range: { start: selection.start, end: selection.end },
      k: 6,
      num_options: 3,
    });
  };

  const handleApplyEdit = (optionId: string) => {
    if (!editSessionId) return;

    applyEditMutation.mutate({
      edit_session_id: editSessionId,
      option_id: optionId,
    });
  };

  const handleExport = async (format: 'markdown' | 'docx') => {
    if (!manuscriptId) return;

    try {
      const blob = await manuscriptApi.export(manuscriptId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `manuscript.${format === 'docx' ? 'docx' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleIngest = async () => {
    if (!manuscriptId) return;

    try {
      await manuscriptApi.ingest(manuscriptId);
      alert('Manuscript processed for embeddings! AI suggestions will now be more accurate.');
    } catch (error) {
      console.error('Ingest failed:', error);
      alert('Failed to process embeddings. Check console for details.');
    }
  };

  const handleUndo = async () => {
    if (!manuscriptId) return;

    try {
      // Get version history
      const history = await manuscriptApi.getHistory(manuscriptId);

      if (!history.versions || history.versions.length < 2) {
        alert('No previous version to undo to.');
        return;
      }

      // Get the previous version (second in the list, since first is current)
      const previousVersion = history.versions[1];

      const confirmed = window.confirm(
        `Undo to previous version?\n\n` +
        `Current: ${history.versions[0].version_tag}\n` +
        `Previous: ${previousVersion.version_tag}\n\n` +
        `This will revert your last change.`
      );

      if (!confirmed) return;

      // Revert to previous version
      await manuscriptApi.revert(manuscriptId, previousVersion.id);

      // Refresh the manuscript content
      await refetchContent();

      alert('Successfully undone last change!');
    } catch (error) {
      console.error('Undo failed:', error);
      alert('Failed to undo. Check console for details.');
    }
  };

  const handleRevertToVersion = async (versionId: string) => {
    if (!manuscriptId) return;

    try {
      await manuscriptApi.revert(manuscriptId, versionId);
      await refetchContent();
      setShowHistory(false);
      alert('Successfully restored to selected version!');
    } catch (error) {
      console.error('Revert failed:', error);
      alert('Failed to restore version. Check console for details.');
    }
  };

  if (!manuscriptId || !manuscriptContent) {
    return <div className={styles.loading}>Loading manuscript...</div>;
  }

  return (
    <div className={styles.editor}>
      <div className={styles.header}>
        <h1>{manuscript?.title || 'Untitled'}</h1>
        <div className={styles.headerActions}>
          <button onClick={handleUndo} className={styles.undoButton}>↶ Undo Last Change</button>
          <button onClick={() => setShowHistory(true)}>📜 View History</button>
          <button onClick={handleIngest}>Process Embeddings</button>
          <button onClick={() => handleExport('markdown')}>Export MD</button>
          <button onClick={() => handleExport('docx')}>Export DOCX</button>
        </div>
      </div>
      
      <div className={styles.content}>
        <div className={styles.leftPane}>
          <ManuscriptViewer
            content={manuscriptContent.content}
            onTextSelection={handleTextSelection}
            selection={selection}
          />
        </div>

        <div className={styles.rightPane}>
          <EditConsole
            selection={selection}
            editOptions={editOptions}
            isLoading={isLoading}
            onSuggestEdits={handleSuggestEdits}
            onApplyEdit={handleApplyEdit}
          />
        </div>
      </div>

      {showHistory && manuscriptId && (
        <VersionHistory
          manuscriptId={manuscriptId}
          onClose={() => setShowHistory(false)}
          onRevert={handleRevertToVersion}
        />
      )}
    </div>
  );
};

export default BookEditor;
