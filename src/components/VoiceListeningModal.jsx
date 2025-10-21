import React from 'react';

const VoiceListeningModal = ({ isOpen, transcript, isFinal, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="voice-modal-overlay">
      <div className="voice-listening-modal">
        <div className="voice-listening-header">
          <div className="voice-mic-icon-animated">🎤</div>
          <h3>Listening...</h3>
        </div>
        
        <div className="voice-transcript-display">
          <p className={isFinal ? 'final' : 'interim'}>
            {transcript || 'Start speaking...'}
          </p>
        </div>

        <div className="voice-modal-hint">
          <small>Say "ok sigma send" to execute the command</small>
        </div>

        <button className="voice-close-button" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
};

export default VoiceListeningModal;
