import React from 'react';
import Editor from '@monaco-editor/react';

interface MonacoDiffViewerProps {
  code: string;
  language?: string;
  highlightLine?: number | null;
  readOnly?: boolean;
  height?: string;
  fileName?: string;
}

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({
  code,
  language = 'python',
  highlightLine = null,
  readOnly = true,
  height = '350px',
  fileName,
}) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#1e1e1e] overflow-hidden shadow-2xl">
      {fileName && (
        <div className="bg-slate-900/90 border-b border-slate-800 px-4 py-2 flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-700"></span>
            <span>{fileName}</span>
          </div>
          <span className="text-[11px] uppercase tracking-wider text-slate-500">{language}</span>
        </div>
      )}
      <Editor
        height={height}
        language={language}
        value={code}
        theme="vs-dark"
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 13,
          lineNumbers: 'on',
          renderLineHighlight: highlightLine ? 'all' : 'line',
          automaticLayout: true,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      />
    </div>
  );
};
