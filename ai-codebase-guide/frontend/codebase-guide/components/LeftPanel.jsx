'use client'

import { useState } from 'react'
import AskTab from './AskTab'
import ImpactTab from './ImpactTab'
import RightPanel from './RightPanel'

export default function LeftPanel() {
  const [activeTab, setActiveTab] = useState('ask')
  const [evidence, setEvidence] = useState([])
  const [totalFiles, setTotalFiles] = useState(null)

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
  <AskTab onEvidenceUpdate={setEvidence} onFilesUpdate={setTotalFiles} />
</div>
<div style={{ display: activeTab === 'impact' ? 'block' : 'none' }}>
  <ImpactTab />
</div>
      </div>

      <RightPanel evidence={evidence} totalFiles={totalFiles} />
    </>
  )
}
