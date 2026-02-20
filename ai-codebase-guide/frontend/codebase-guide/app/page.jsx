'use client'

import { useState } from 'react'
import TopBar from '../components/TopBar'
import LeftPanel from '../components/LeftPanel'
import RightPanel from '../components/RightPanel'

export default function Page() {
  const [theme, setTheme] = useState('dark')

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  return (
    <div className="app" data-theme={theme}>
      <TopBar theme={theme} toggleTheme={toggleTheme} />
      <div className="main-layout">
        <LeftPanel />
        <RightPanel />
      </div>
    </div>
  )
}
