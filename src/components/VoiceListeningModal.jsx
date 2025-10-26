import React from 'react';

const MicIcon = ({ size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <rect x="9" y="3" width="6" height="12" rx="3" stroke="currentColor" strokeWidth="1.8" />
    <path d="M5 11a7 7 0 0 0 14 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    <path d="M12 19v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    <path d="M8 22h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const CloseIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M6 6l12 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    <path d="M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
  </svg>
);

const HintIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M12 3a6 6 0 0 1 4 10.39V16a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.61A6 6 0 0 1 12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M10 20h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    <path d="M11 22h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
  </svg>
);

const CheckIcon = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M6 12.5l4 4 8-9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const VoiceListeningModal = ({ isOpen, transcript, isFinal, onClose }) => {
  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    // Close only if clicking on the overlay itself, not the modal
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="voice-modal-overlay" onClick={handleOverlayClick}>
      <div className="voice-listening-modal">
        <div className="voice-listening-header">
          <div className="voice-mic-icon-animated" aria-hidden="true">
            <MicIcon size={32} />
          </div>
          <h3>Listening...</h3>
          <button 
            className="voice-modal-close-icon" 
            onClick={onClose}
            aria-label="Close"
          >
            <CloseIcon size={16} />
          </button>
        </div>
        
        <div className="voice-transcript-display">
          <p className={isFinal ? 'final' : 'interim'}>
            {transcript || 'Start speaking...'}
          </p>
        </div>

        <div className="voice-modal-hint">
          <small>
            <span className="inline-icon" aria-hidden="true"><HintIcon size={14} /></span>
            Say "ok sigma send" followed by your command to auto-execute
          </small>
          <small>Or just speak and click Done</small>
        </div>

        <div className="voice-modal-buttons">
          <button className="voice-close-button" onClick={onClose}>
            <span className="inline-icon" aria-hidden="true"><CheckIcon size={16} /></span>
            Done
          </button>
          <button className="voice-cancel-button" onClick={onClose}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: '0.5rem'}}>
              <path d="M6 6l12 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceListeningModal;
