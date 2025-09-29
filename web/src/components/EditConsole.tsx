import React, { useState } from 'react';
import { EditOption } from '../lib/api';
import DiffViewer from './DiffViewer';
import styles from './EditConsole.module.css';

interface Selection {
  start: number;
  end: number;
  text: string;
}

interface EditConsoleProps {
  selection: Selection | null;
  editOptions: EditOption[];
  isLoading: boolean;
  onSuggestEdits: (instruction: string) => void;
  onApplyEdit: (optionId: string) => void;
}

const PRESET_INSTRUCTIONS = [
  'Tighten and improve clarity',
  'Add more suspense and tension',
  'Improve flow and transitions',
  'Make more concise',
  'Enhance descriptive language',
  'Fix grammar and style issues',
];

const EditConsole: React.FC<EditConsoleProps> = ({
  selection,
  editOptions,
  isLoading,
  onSuggestEdits,
  onApplyEdit,
}) => {
  const [instruction, setInstruction] = useState('');
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);

  const handleSuggest = () => {
    if (!instruction.trim() || !selection) return;
    onSuggestEdits(instruction.trim());
  };

  const handlePresetClick = (preset: string) => {
    setInstruction(preset);
  };

  const handleApply = (optionId: string) => {
    if (window.confirm('Apply this edit to the manuscript?')) {
      onApplyEdit(optionId);
    }
  };

  return (
    <div className={styles.console}>
      <div className={styles.header}>
        <h3>Edit Console</h3>
      </div>

      {!selection ? (
        <div className={styles.noSelection}>
          <p>Select text in the manuscript to start editing</p>
        </div>
      ) : (
        <div className={styles.content}>
          <div className={styles.selectionPreview}>
            <h4>Selected Text</h4>
            <div className={styles.selectedText}>
              {selection.text.length > 200 
                ? `${selection.text.substring(0, 200)}...` 
                : selection.text}
            </div>
            <div className={styles.selectionMeta}>
              {selection.text.length} characters ({selection.start}-{selection.end})
            </div>
          </div>

          <div className={styles.instructionSection}>
            <h4>Editing Instruction</h4>
            <textarea
              className={styles.instructionInput}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Describe how you want to edit this text..."
              rows={3}
            />
            
            <div className={styles.presets}>
              <div className={styles.presetsLabel}>Quick presets:</div>
              <div className={styles.presetButtons}>
                {PRESET_INSTRUCTIONS.map((preset) => (
                  <button
                    key={preset}
                    className={styles.presetButton}
                    onClick={() => handlePresetClick(preset)}
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <button
              className={styles.suggestButton}
              onClick={handleSuggest}
              disabled={!instruction.trim() || isLoading}
            >
              {isLoading ? 'Generating...' : 'Get Suggestions'}
            </button>
          </div>

          {editOptions.length > 0 && (
            <div className={styles.optionsSection}>
              <h4>Edit Options</h4>
              <div className={styles.options}>
                {editOptions.map((option) => (
                  <div key={option.option_id} className={styles.option}>
                    <div className={styles.optionHeader}>
                      <span className={styles.optionLabel}>Option {option.label}</span>
                      <span className={styles.optionSeverity}>{option.severity}</span>
                    </div>
                    
                    <DiffViewer
                      before={option.before}
                      after={option.after}
                      isExpanded={selectedOptionId === option.option_id}
                      onToggle={() => setSelectedOptionId(
                        selectedOptionId === option.option_id ? null : option.option_id
                      )}
                    />
                    
                    <div className={styles.optionActions}>
                      <button
                        className={styles.applyButton}
                        onClick={() => handleApply(option.option_id)}
                      >
                        Apply This Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EditConsole;
