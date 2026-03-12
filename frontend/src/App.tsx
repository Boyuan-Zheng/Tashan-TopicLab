import { Routes, Route } from 'react-router-dom'
import TopNav from './components/TopNav'
import TopicList from './pages/TopicList'
import CreateTopic from './pages/CreateTopic'
import TopicDetail from './pages/TopicDetail'
import ExpertList from './pages/ExpertList'
import ExpertEdit from './pages/ExpertEdit'
import SkillLibrary from './pages/SkillLibrary'
import MCPLibrary from './pages/MCPLibrary'
import ModeratorModeLibrary from './pages/ModeratorModeLibrary'
import ProfileHelperPage from './pages/ProfileHelperPage'
import AgentLinkLibraryPage from './pages/AgentLinkLibraryPage'
import AgentLinkChatPage from './pages/AgentLinkChatPage'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <>
      <TopNav />
      <main className="pt-14 pb-[env(safe-area-inset-bottom)] min-h-screen">
        <Routes>
          <Route path="/" element={<TopicList />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/topics/new" element={<CreateTopic />} />
          <Route path="/topics/:id" element={<TopicDetail />} />
          <Route path="/experts" element={<ExpertList />} />
          <Route path="/experts/:name/edit" element={<ExpertEdit />} />
          <Route path="/skills" element={<SkillLibrary />} />
          <Route path="/mcp" element={<MCPLibrary />} />
          <Route path="/moderator-modes" element={<ModeratorModeLibrary />} />
          <Route path="/profile-helper/*" element={<ProfileHelperPage />} />
          <Route path="/agent-links" element={<AgentLinkLibraryPage />} />
          <Route path="/agent-links/:slug" element={<AgentLinkChatPage />} />
        </Routes>
      </main>
    </>
  )
}

export default App
