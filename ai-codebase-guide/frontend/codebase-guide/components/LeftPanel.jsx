'use client'

import { useState } from 'react'
import AskTab from './AskTab'
import ImpactTab from './ImpactTab'

export default function LeftPanel() {
  const [activeTab, setActiveTab] = useState('ask')

  return (
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

      {activeTab === 'ask' && <AskTab />}
      {activeTab === 'impact' && <ImpactTab />}
    </div>
  )
}
