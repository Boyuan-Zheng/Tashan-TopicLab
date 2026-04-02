import { Link } from 'react-router-dom'
import { ALL_SCALES } from '../data/scales'

export function ScalesPage() {
  return (
    <div className="scales-page">
      <div className="scales-grid">
        {ALL_SCALES.map((scale) => (
          <Link key={scale.id} to={`/profile-helper/scales/${scale.id}`} className="scale-card">
            <h3>{scale.name}</h3>
            <p>{scale.description}</p>
            <span className="scale-card-action">开始测试 →</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
