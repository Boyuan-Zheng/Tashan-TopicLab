import { Link } from 'react-router-dom'
import { ALL_SCALES } from '../data/scales'

export function ScalesPage() {
  return (
    <div className="scales-page">
      <header className="scales-header">
        <h2>量表测试</h2>
        <p>通过标准化量表评估科研认知风格与学术动机，可用于校对数字分身推断结果。</p>
      </header>

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
