import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { mockSecurityVulnerabilities, SecurityVulnerability } from '@/services/mockData';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Download,
  AlertTriangle,
  Search,
  ExternalLink,
  Wrench,
  CheckCircle2,
  FileCode,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const SecurityReports: React.FC = () => {
  const navigate = useNavigate();
  const { success, info } = useToast();
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const filteredVulnerabilities = mockSecurityVulnerabilities.filter((v) => {
    const matchesSearch =
      v.title.toLowerCase().includes(search.toLowerCase()) ||
      v.filePath.toLowerCase().includes(search.toLowerCase()) ||
      v.owaspTag.toLowerCase().includes(search.toLowerCase());
    const matchesSeverity = severityFilter === 'all' || v.severity === severityFilter;
    return matchesSearch && matchesSeverity;
  });

  const handleExportSarif = () => {
    const sarifBlob = new Blob([JSON.stringify({ version: '2.1.0', runs: filteredVulnerabilities }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(sarifBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openreview-security-report.sarif.json';
    a.click();
    success('Report Exported', 'SARIF v2.1 format downloaded successfully.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Security & Vulnerability Intelligence</h1>
            <Badge variant="destructive">OWASP Top 10 Scans</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Automated deep security analysis detecting injection flaws, secret leaks, and access control gaps.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportSarif}
            className="flex items-center gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export SARIF / JSON</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={() => navigate('/autofix')}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Wrench className="w-3.5 h-3.5 text-amber-300" />
            <span>Remediate in AutoFix</span>
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Critical CVEs</span>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">2</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Blocking automated merge</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>High Severity</span>
              <span className="w-2 h-2 rounded-full bg-amber-500" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400">2</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Remediation in progress</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Security Score</span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">88.5/100</div>
            <p className="text-[11px] text-slate-500 mt-0.5">SOC2 compliance target: &gt;85</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Resolved Issues</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-sky-400">14</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Patched across 3 repositories</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <Input
            placeholder="Search by vulnerability, file path, or OWASP tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs bg-[#0b101c]"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-[#0e1422] p-1 rounded-lg border border-slate-800 text-xs">
          {['all', 'critical', 'high', 'medium', 'resolved'].map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`px-2.5 py-1 rounded capitalize text-[11px] transition ${
                severityFilter === s
                  ? 'bg-sky-500/20 text-sky-400 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Vulnerabilities List */}
      <div className="space-y-3">
        {filteredVulnerabilities.map((vuln: SecurityVulnerability) => (
          <Card key={vuln.id} className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700/80 transition">
            <CardContent className="p-5">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={vuln.severity === 'critical' ? 'destructive' : vuln.severity === 'high' ? 'warning' : 'secondary'}
                    className="uppercase text-[10px]"
                  >
                    {vuln.severity}
                  </Badge>
                  <span className="text-xs font-mono font-semibold text-slate-300">{vuln.cveId || vuln.category}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono">
                    {vuln.owaspTag}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                  <FileCode className="w-3.5 h-3.5 text-slate-500" />
                  <span>{vuln.filePath}#L{vuln.lineNumber}</span>
                </div>
              </div>

              <h3 className="font-semibold text-white text-sm mb-1">{vuln.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">{vuln.description}</p>

              {vuln.remediationSnippet && (
                <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800 font-mono text-[11px] text-emerald-400 mb-3">
                  <div className="text-[10px] uppercase text-slate-500 mb-1">Suggested Automated Fix</div>
                  <code>{vuln.remediationSnippet}</code>
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                <div className="text-slate-500 text-[11px] font-mono">
                  Detected in <span className="text-slate-300">{vuln.repository}</span> • {vuln.detectedAt}
                </div>
                <Button
                  size="sm"
                  variant="electric"
                  onClick={() => navigate('/autofix')}
                  className="flex items-center gap-1.5 text-xs font-semibold"
                >
                  <Wrench className="w-3 h-3 text-amber-300" />
                  <span>Review AutoFix</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
