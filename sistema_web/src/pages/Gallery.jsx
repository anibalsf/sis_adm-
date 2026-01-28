export default function Gallery() {
  const items = [
    { id: 1, type: 'IMAGE', url: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?q=80&w=1200&auto=format&fit=crop', title: 'Flota Moderna' },
    { id: 2, type: 'IMAGE', url: 'https://images.unsplash.com/photo-1533240332313-0db49b459ad6?q=80&w=1200&auto=format&fit=crop', title: 'Cascadas Tunki' },
    { id: 3, type: 'IMAGE', url: 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?q=80&w=1200&auto=format&fit=crop', title: 'Rutas Yungas' },
  ]
  return (
    <div className="page">
      <h2>Galería</h2>
      <div className="grid">
        {items.map(item => (
          <div key={item.id} className="card">
            <img src={item.url} alt={item.title} />
            <div className="card-title">{item.title}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
