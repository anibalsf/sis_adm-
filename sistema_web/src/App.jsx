import { Routes, Route, Link, Navigate } from 'react-router-dom'
import Gallery from './pages/Gallery.jsx'

function Home() {
  return (
    <div className="hero">
      <h1>Sindicato Taipiplaya</h1>
      <p>Servicios de Transporte y Turismo</p>
      <div className="cta-row">
        <Link to="/galeria" className="btn">Ver Galería</Link>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="layout">
      <nav className="nav">
        <div className="brand">Sistema Web</div>
        <div className="links">
          <Link to="/">Inicio</Link>
          <Link to="/galeria">Galería</Link>
        </div>
      </nav>
      <main className="content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/galeria" element={<Gallery />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
      <footer className="footer">
        © {new Date().getFullYear()} Taipiplaya
      </footer>
    </div>
  )
}
