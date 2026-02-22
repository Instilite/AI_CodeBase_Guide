'use client'

import { useState } from 'react'
import AskTab from './AskTab'
import ImpactTab from './ImpactTab'
import RightPanel from './RightPanel'

export default function LeftPanel({ selectedRepoId, disabledReason }) {
  const [activeTab, setActiveTab] = useState('ask')
  const [evidence, setEvidence] = useState([])
  const [totalFiles, setTotalFiles] = useState(null)
  const [activeEvidenceId, setActiveEvidenceId] = useState(null)

  const handleEvidenceUpdate = (nextEvidence) => {
    setEvidence(Array.isArray(nextEvidence) ? nextEvidence : [])
    setActiveEvidenceId(null)
  }

  const handleImpactEvidenceUpdate = (nextEvidence) => {
    setTotalFiles(null)
    handleEvidenceUpdate(nextEvidence)
  }

  return (
    <>
      <div className="left-panel">
        <div className="tabs">
          <div
            className={`tab ${activeTab === 'ask' ? 'active' : ''}`}
            onClick={() => setActiveTab('ask')}
          >
            Ask
          </div>
          <div
            className={`tab ${activeTab === 'impact' ? 'active' : ''}`}
            onClick={() => setActiveTab('impact')}
          >
            Impact
          </div>
        </div>

        <div style={{ display: activeTab === 'ask' ? 'flex' : 'none', flexDirection: 'column', flex: 1 }}>
          <AskTab
            selectedRepoId={selectedRepoId}
            disabledReason={disabledReason}
            onEvidenceUpdate={handleEvidenceUpdate}
            onFilesUpdate={setTotalFiles}
            onEvidenceSelect={setActiveEvidenceId}
          />
        </div>

        <div style={{ display: activeTab === 'impact' ? 'flex' : 'none', flexDirection: 'column', flex: 1 }}>
          <ImpactTab
            selectedRepoId={selectedRepoId}
            disabledReason={disabledReason}
            onEvidenceUpdate={handleImpactEvidenceUpdate}
            onEvidenceSelect={setActiveEvidenceId}
          />
        </div>
      </div>

      <RightPanel
        evidence={evidence}
        totalFiles={totalFiles}
        activeEvidenceId={activeEvidenceId}
        onEvidenceSelect={setActiveEvidenceId}
      />
    </>
  )
}
