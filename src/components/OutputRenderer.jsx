import React, { useState } from 'react';
import './OutputRenderer.css';

/**
 * Advanced Output Renderer
 * Displays beautifully formatted AI-powered command outputs
 */

const OutputRenderer = ({ response, command }) => {
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [searchFilter, setSearchFilter] = useState('');

  if (!response) return null;

  const type = response.type || 'text';

  // ==================== FILE LISTING ====================
  if (type === 'file_listing') {
    const files = response.data || [];
    const summary = response.summary || {};
    const filteredFiles = files.filter(f => 
      f.name.toLowerCase().includes(searchFilter.toLowerCase())
    );

    return (
      <div className="output-file-listing">
        <div className="output-header">
          <h3>📁 File Listing</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <div className="listing-stats">
          <div className="stat-card">
            <span className="stat-icon">📊</span>
            <div>
              <span className="stat-label">Total Items</span>
              <span className="stat-value">{summary.total_items || 0}</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📁</span>
            <div>
              <span className="stat-label">Directories</span>
              <span className="stat-value">{summary.directories || 0}</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📄</span>
            <div>
              <span className="stat-label">Files</span>
              <span className="stat-value">{summary.files || 0}</span>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">💾</span>
            <div>
              <span className="stat-label">Total Size</span>
              <span className="stat-value">{summary.total_size_human || '0 B'}</span>
            </div>
          </div>
        </div>

        <div className="listing-search">
          <input 
            type="text"
            placeholder="🔍 Search files..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="search-input"
          />
          <span className="search-count">{filteredFiles.length} results</span>
        </div>

        <div className="files-table">
          <div className="table-header">
            <div className="col-icon">Type</div>
            <div className="col-name">Name</div>
            <div className="col-size">Size</div>
            <div className="col-date">Date Modified</div>
            <div className="col-perms">Permissions</div>
          </div>
          
          <div className="table-body">
            {filteredFiles.map((file, idx) => (
              <div key={idx} className={`table-row ${file.is_directory ? 'is-dir' : ''}`}>
                <div className="col-icon">{file.icon}</div>
                <div className="col-name">
                  <span className="file-name">{file.name}</span>
                  {file.is_symlink && <span className="symlink-badge">→ link</span>}
                </div>
                <div className="col-size">
                  <span className={`size-badge ${file.size > 1000000 ? 'large' : ''}`}>
                    {formatBytes(parseInt(file.size) || 0)}
                  </span>
                </div>
                <div className="col-date">{file.date}</div>
                <div className="col-perms">
                  <code className="perms">{file.permissions}</code>
                </div>
              </div>
            ))}
          </div>
        </div>

        {response.actions && (
          <div className="output-actions">
            {response.actions.map((action, idx) => (
              <button key={idx} className={`action-button ${action.type}`}>
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ==================== DISK USAGE ====================
  if (type === 'disk_usage') {
    const disks = response.data || [];
    const summary = response.summary || {};
    const hasWarning = response.warning;

    return (
      <div className="output-disk-usage">
        <div className="output-header">
          <h3>💿 Disk Usage</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        {hasWarning && (
          <div className="warning-banner">
            <span className="warning-icon">⚠️</span>
            <span>Disk usage is critically high! Consider freeing up space.</span>
          </div>
        )}

        <div className="disk-summary">
          <div className="summary-item">
            <span className="summary-label">Total Used</span>
            <span className="summary-value">{summary.total_used}</span>
            <span className="summary-percent">{summary.usage_percent}%</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Total Free</span>
            <span className="summary-value">{summary.total_free}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Total Size</span>
            <span className="summary-value">{summary.total_size}</span>
          </div>
        </div>

        <div className="disks-list">
          {disks.map((disk, idx) => (
            <div key={idx} className={`disk-card ${disk.usage_level}`}>
              <div className="disk-header">
                <span className="disk-name">{disk.filesystem}</span>
                <span className="disk-percent">{disk.usage_percent}%</span>
              </div>
              <div className="disk-progress">
                <div className="progress-bar" style={{ width: `${disk.usage_percent}%` }} />
              </div>
              <div className="disk-stats">
                <span className="stat">Used: {disk.used}</span>
                <span className="stat">Available: {disk.available}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ==================== SYSTEM INFO ====================
  if (type === 'system_info') {
    const data = response.data || {};

    return (
      <div className="output-system-info">
        <div className="output-header">
          <h3>🖥️ System Information</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <div className="info-grid">
          {Object.entries(data).slice(0, 12).map(([key, value], idx) => (
            <div key={idx} className="info-card">
              <span className="info-label">{key}</span>
              <span className="info-value">{String(value).substring(0, 50)}</span>
            </div>
          ))}
        </div>

        {Object.keys(data).length > 12 && (
          <button className="show-more-button">Show {Object.keys(data).length - 12} more</button>
        )}
      </div>
    );
  }

  // ==================== PROCESS LIST ====================
  if (type === 'process_list') {
    const processes = response.data || [];

    return (
      <div className="output-process-list">
        <div className="output-header">
          <h3>⚙️ Running Processes</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <div className="process-stats">
          <span className="stat">Total: {response.total_processes}</span>
          <span className="stat">Showing: {processes.length}</span>
          {response.has_more && <span className="stat">+{response.total_processes - processes.length} more</span>}
        </div>

        <div className="processes-list">
          {processes.map((proc, idx) => (
            <div key={idx} className="process-item">
              <span className="process-pid">{proc.pid}</span>
              <span className="process-cmd">{proc.command.substring(0, 80)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ==================== ERROR OUTPUT ====================
  if (type === 'error') {
    const suggestions = response.suggestions || [];

    return (
      <div className="output-error">
        <div className="error-banner">
          <span className="error-icon">❌</span>
          <div className="error-content">
            <h3>Error: {response.error_type?.replace(/_/g, ' ')}</h3>
            <p className="error-message">{response.message}</p>
          </div>
        </div>

        {suggestions.length > 0 && (
          <div className="error-suggestions">
            <h4>💡 Suggestions to fix this:</h4>
            <ul>
              {suggestions.map((suggestion, idx) => (
                <li key={idx}>{suggestion}</li>
              ))}
            </ul>
          </div>
        )}

        <details className="error-details">
          <summary>View full error details</summary>
          <pre className="error-trace">{response.details}</pre>
        </details>
      </div>
    );
  }

  // ==================== SUCCESS OUTPUT ====================
  if (type === 'success') {
    return (
      <div className="output-success">
        <div className="success-banner">
          <span className="success-icon">✅</span>
          <div className="success-content">
            <h3>{response.message}</h3>
            <p>{response.explanation}</p>
          </div>
        </div>
      </div>
    );
  }

  // ==================== TABLE DATA ====================
  if (type === 'table') {
    const headers = response.headers || [];
    const rows = response.rows || [];

    return (
      <div className="output-table">
        <div className="output-header">
          <h3>📋 Table Data</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                {headers.map((header, idx) => (
                  <th key={idx}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="table-count">{rows.length} rows × {headers.length} columns</p>
      </div>
    );
  }

  // ==================== JSON DATA ====================
  if (type === 'json') {
    const data = response.data || {};

    return (
      <div className="output-json">
        <div className="output-header">
          <h3>📦 JSON Data</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <pre className="json-viewer">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  // ==================== NETWORK INFO ====================
  if (type === 'network_info') {
    const interfaces = response.data || [];

    return (
      <div className="output-network">
        <div className="output-header">
          <h3>🌐 Network Information</h3>
          <p className="explanation">{response.explanation}</p>
        </div>

        <div className="interfaces-grid">
          {interfaces.map((iface, idx) => (
            <div key={idx} className="interface-card">
              <h4>{iface.name}</h4>
              <div className="interface-details">
                {Object.entries(iface.details).slice(0, 5).map(([key, value], didx) => (
                  <div key={didx} className="detail-row">
                    <span className="detail-key">{key}:</span>
                    <span className="detail-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ==================== TEXT OUTPUT ====================
  return (
    <div className="output-text">
      <div className="output-header">
        <h3>📝 Output</h3>
        <p className="explanation">{response.explanation}</p>
      </div>

      <div className="output-stats">
        <span className="stat">Lines: {response.line_count || 1}</span>
        <span className="stat">Characters: {response.character_count || 0}</span>
      </div>

      <pre className="text-output">
        {response.content || response.raw_output || '(No output)'}
      </pre>
    </div>
  );
};

// Utility function to format bytes
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default OutputRenderer;
