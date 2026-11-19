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
    <div className="rounded-[2px] border border-[#26221c] bg-[#12100d] overflow-hidden shadow-2xl flex flex-col">
      {/* Editor Header Bar */}
      <div className="bg-[#171511] border-b border-[#24201a] px-4 py-2 flex items-center justify-between text-xs font-mono text-[#8a8378]">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#c75a4a]" />
            <span className="w-2 h-2 rounded-full bg-[#e29b38]" />
            <span className="w-2 h-2 rounded-full bg-[#5a9e6f]" />
          </div>
          {fileName && (
            <span className="text-[#f5f0e6] font-medium tracking-tight ml-1 text-xs">
              {fileName}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {isDiffMode && originalCode && (
            <div className="flex items-center rounded-[2px] bg-[#12100d] border border-[#26221c] p-0.5 text-[11px]">
              <button
                type="button"
                onClick={() => setSplitView(true)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded-[2px] transition ${
                  splitView ? 'bg-[#221f1a] text-[#d4a853] font-medium border border-[#38332a]' : 'text-[#8a8378] hover:text-[#d8d2c4]'
                }`}
              >
                <Split className="w-3 h-3" />
                <span>Side-by-side</span>
              </button>
              <button
                type="button"
                onClick={() => setSplitView(false)}
                className={`flex items-center gap-1 px-2 py-0.5 rounded-[2px] transition ${
                  !splitView ? 'bg-[#221f1a] text-[#d4a853] font-medium border border-[#38332a]' : 'text-[#8a8378] hover:text-[#d8d2c4]'
                }`}
              >
                <AlignJustify className="w-3 h-3" />
                <span>Inline</span>
              </button>
            </div>
          )}

          <span className="text-[10px] uppercase font-mono tracking-wider text-[#6a6358]">
            {language}
          </span>

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 text-[11px] font-mono text-[#8a8378] hover:text-[#f5f0e6] transition px-2 py-0.5 rounded-[2px] hover:bg-[#201d18]"
            title="Copy code to clipboard"
          >
            {copied ? <Check className="w-3 h-3 text-[#5a9e6f]" /> : <Copy className="w-3 h-3" />}
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
              fontSize: 12,
              automaticLayout: true,
              fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
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
              fontSize: 12,
              lineNumbers: 'on',
              renderLineHighlight: highlightLine ? 'all' : 'line',
              automaticLayout: true,
              fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
            }}
          />
        )}
      </div>
    </div>
  );
};
