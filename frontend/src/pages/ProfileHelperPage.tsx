import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { ChatPage } from '../modules/profile-helper/pages/ChatPage'
import { ProfilePage } from '../modules/profile-helper/pages/ProfilePage'
import { ScalesPage } from '../modules/profile-helper/pages/ScalesPage'
import { ScaleTestPage } from '../modules/profile-helper/pages/ScaleTestPage'
import '../modules/profile-helper/profile-helper.css'

function ProfileHelperNav() {
  const location = useLocation()
  const base = '/profile-helper'
  const isChat = location.pathname === base || location.pathname === `${base}/`
  const isProfile = location.pathname.startsWith(`${base}/profile`)
  const isScales = location.pathname.startsWith(`${base}/scales`)

  return (
    <div className="ph-subnav">
      <div className="ph-subnav-title">目录</div>
      <Link to={base} className={`ph-subnav-link ${isChat ? 'active' : ''}`}>
        对话采集
      </Link>
      <Link to={`${base}/profile`} className={`ph-subnav-link ${isProfile ? 'active' : ''}`}>
        我的分身
      </Link>
      <Link to={`${base}/scales`} className={`ph-subnav-link ${isScales ? 'active' : ''}`}>
        量表测试
      </Link>
    </div>
  )
}

export default function ProfileHelperPage() {
  const location = useLocation()
  const base = '/profile-helper'
  const isChat = location.pathname === base || location.pathname === `${base}/`

  return (
    <div className="profile-helper-page">
      <div className="ph-layout">
        <ProfileHelperNav />
        <div className={`ph-content ${isChat ? 'ph-content-chat' : 'ph-content-flow'}`}>
          <Routes>
            <Route index element={<ChatPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="scales" element={<ScalesPage />} />
            <Route path="scales/:scaleId" element={<ScaleTestPage />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}
