import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, API_URL } from '../services/api'

function PrintHojaRuta(){
  const [params] = useSearchParams()
  const id = params.get('id')
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(()=>{
    const run = async()=>{
      try{
        const res = await api.getHojaRuta(id)
        let u = res.data?.archivo_url || ''
        if(!u){
          const gen = await api.generarPdfHoja(id)
          u = gen.data?.archivo_url || ''
        }
        if(u){
          const backendOrigin = new URL(API_URL).origin
          if (u.startsWith('/')) {
            u = `${backendOrigin}${u}`
          } else {
            try {
              const parsed = new URL(u, backendOrigin)
              const needsPortFix =
                (parsed.hostname === '127.0.0.1' || parsed.hostname === 'localhost') &&
                (!parsed.port || parsed.port === '')
              if (needsPortFix) {
                u = `${backendOrigin}${parsed.pathname}${parsed.search || ''}${parsed.hash || ''}`
              }
            } catch {
              // Si la URL es inválida, forzar a backendOrigin + u
              u = `${backendOrigin}${u.startsWith('/') ? '' : '/'}${u}`
            }
          }
          setUrl(u)
          setTimeout(()=>{ window.print() }, 500)
        }else{
          setError('No se pudo generar el PDF')
        }
      }catch(err){ setError('Error al cargar comprobante'); console.error(err) }
    }
    if(id) run()
  },[id])

  return (
    <div style={{padding:0, margin:0}}>
      {error ? (<div className="error" style={{padding:'20px'}}>{error}</div>) : url ? (
        <embed src={url} type="application/pdf" style={{width:'100vw', height:'100vh'}} />
      ) : (
        <div style={{padding:'20px'}}>Generando comprobante...</div>
      )}
    </div>
  )
}

export default PrintHojaRuta
