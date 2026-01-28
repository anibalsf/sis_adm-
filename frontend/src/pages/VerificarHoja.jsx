import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'

function VerificarHoja() {
    const { id } = useParams()
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        const fetch = async () => {
            try {
                // Usamos una llamada directa a axios o fetch si el api wrapper requiere auth
                // Pero como el endpoint es público, deberíamos poder usar api.get si no fuerza auth headers o si el backend los ignora
                // Para asegurar, usaremos fetch directo al endpoint público
                const res = await api.validarQr(id)
                setData(res.data)
            } catch (err) {
                setError('Hoja de ruta no válida o no encontrada')
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetch()
    }, [id])

    if (loading) return <div className="p-4 text-center">Verificando...</div>
    if (error) return (
        <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
            <div className="bg-white p-6 rounded-lg shadow-lg text-center max-w-sm w-full">
                <div className="text-red-500 text-5xl mb-4">✕</div>
                <h2 className="text-xl font-bold text-red-700 mb-2">Verificación Fallida</h2>
                <p className="text-gray-600">{error}</p>
            </div>
        </div>
    )

    const isValid = data.estado === 'emitida' || data.estado === 'pagada'
    const color = isValid ? 'green' : 'red'
    const icon = isValid ? '✓' : '✕'
    const title = isValid ? 'HOJA DE RUTA VÁLIDA' : 'HOJA NO VÁLIDA'

    return (
        <div className="min-h-screen bg-body flex items-center justify-center p-4">
            <div className="card max-w-md w-full overflow-hidden" style={{ padding: 0 }}>
                <div className={`bg-${color} p-8 text-center`} style={{ background: `var(--${color === 'green' ? 'success' : 'danger'})` }}>
                    <div className="text-white text-7xl font-bold mb-3">{icon}</div>
                    <h1 className="text-2xl font-bold text-white">{title}</h1>
                    <p className="text-white opacity-90 mt-1 font-semibold">Nº {data.nro}</p>
                </div>

                <div className="p-8 space-y-6">
                    <div>
                        <label className="text-xs text-muted uppercase block mb-1 font-bold">Estado de la Hoja</label>
                        <span className={`badge badge-${data.estado} text-lg py-1 px-4`}>{data.estado.toUpperCase()}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="text-xs text-muted uppercase block mb-1 font-bold">Fecha Salida</label>
                            <p className="font-bold text-lg color-main">{data.fecha_salida}</p>
                        </div>
                        <div>
                            <label className="text-xs text-muted uppercase block mb-1 font-bold">Monto Pagado</label>
                            <p className="font-bold text-lg color-main">Bs. {data.monto}</p>
                        </div>
                    </div>

                    <div>
                        <label className="text-xs text-muted uppercase block mb-1 font-bold">Ruta / Destino</label>
                        <p className="font-bold text-xl color-primary">{data.ruta}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="text-xs text-muted uppercase block mb-1 font-bold">Vehículo</label>
                            <p className="font-bold color-main">{data.vehiculo}</p>
                        </div>
                        <div>
                            <label className="text-xs text-muted uppercase block mb-1 font-bold">Afiliado</label>
                            <p className="font-bold color-main">{data.afiliado}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-surface-alt p-6 text-center text-sm text-muted border-t border-subtle">
                    <img src="/logo_smit.jpg" alt="Logo" style={{ width: '100px', marginBottom: '10px' }} />
                    <p className="font-bold">Sindicato Mixto Integración Taipiplaya</p>
                    <p className="opacity-75">Verificación Digital Segura</p>
                </div>
            </div>
        </div>
    )
}

export default VerificarHoja
