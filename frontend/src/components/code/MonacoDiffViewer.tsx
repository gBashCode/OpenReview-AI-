import React, { useState } from 'react';
import Editor, { DiffEditor } from '@monaco-editor/react';
import { Copy, Check, Split, AlignJustify } from 'lucide-react';
import { useToast } from '../ui/toast';

interface MonacoDiffViewerProps {
  code: string;
  originalCode?: string;
  language?: string;
  highlightLine?: number | null;
  readOnly?: boolean;
  height?: string;
  fileName?: string;
  isDiffMode?: boolean;
  onCodeChange?: (newCode: string) => void;
}

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({
  code,
  originalCode,
  language = 'python',
  highlightLine = null,
  readOnly = true,
  height = '380px',
  fileName,
  isDiffMode = false,
  onCodeChange,
}) => {
  const [copied, setCopied] = useState(false);
  const [splitView, setSplitView] = useState(true);
  const { success } = useToast();

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    success('Copied to Clipboard', `Code from ${fileName || 'editor'} copied.`);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-slate-800/90 bg-[#0c101c] overflow-hidden shadow-2xl flex flex-col">
      {/* Editor Header Bar */}
      <div className="bg-[#0f1422] border-b border-slate-800/80 px-4 py-2 flex items-center justify-between text-xs font-mono text-slate-400">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          {fileName && (
            <span className="text-slate-300 font-semibold tracking-tight ml-1 text-xs">
              {fileName}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {isDiffMode && originalCode && (
            <div className="flex items-center rounded-md bg-slate-900 border border-slate-800 p-0.5 text-[11px]">
              <button
                type="button"
                onClick={() => setSplitView(true)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded transition ${
                  splitView ? 'bg-sky-500/20 text-sky-400 font-semibold' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Split className="w-3 h-3" />
                <span>Side-by-side</span>
              </button>
              <button
                type="button"
                onClick={() => setSplitView(false)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded transition ${
                  !splitView ? 'bg-sky-500/20 text-sky-400 font-semibold' : 'text-slate-400 hover:text-white'
                }`}
              >
                <AlignJustify className="w-3 h-3" />
                <span>Inline</span>
              </button>
            </div>
          )}

          <span className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">
            {language}
          </span>

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white transition px-2 py-1 rounded hover:bg-slate-800"
            title="Copy code to clipboard"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Monaco Editor Render */}
      <div className="relative">
        {isDiffMode && originalCode ? (
          <DiffEditor
            height={height}
            original={originalCode}
            modified={code}
            language={language}
            theme="vs-dark"
            options={{
              readOnly,
              renderSideBySide: splitView,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 12.5,
              automaticLayout: true,
              fontFamily: "'JetBrains Mono', monospace",
              lineNumbers: 'on',
              renderIndicators: true,
            }}
          />
        ) : (
          <Editor
            height={height}
            language={language}
            value={code}
            onChange={(val) => onCodeChange?.(val || '')}
            theme="vs-dark"
            options={{
              readOnly,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 12.5,
              lineNumbers: 'on',
              renderLineHighlight: highlightLine ? 'all' : 'line',
              automaticLayout: true,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          />
        )}
      </div>
    </div>
  );
};
