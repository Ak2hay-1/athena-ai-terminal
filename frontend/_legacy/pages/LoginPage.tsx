import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    // #region agent log
    fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'300484'},body:JSON.stringify({sessionId:'300484',runId:'pre-fix',hypothesisId:'E',location:'_legacy/LoginPage.tsx:onSubmit',message:'legacy login submit',data:{usernameLen:username.length,passwordLen:password.length,href:window.location.href},timestamp:Date.now()})}).catch(()=>{})
    // #endregion

    try {
      await login(username, password)
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'300484'},body:JSON.stringify({sessionId:'300484',runId:'pre-fix',hypothesisId:'D',location:'_legacy/LoginPage.tsx:onSubmit',message:'legacy login ok',data:{},timestamp:Date.now()})}).catch(()=>{})
      // #endregion
      await refreshUser()
      navigate('/')
    } catch (err) {
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'300484'},body:JSON.stringify({sessionId:'300484',runId:'pre-fix',hypothesisId:'A',location:'_legacy/LoginPage.tsx:onSubmit',message:'legacy login catch',data:{error:err instanceof Error?err.message:String(err)},timestamp:Date.now()})}).catch(()=>{})
      // #endregion
      setError('Invalid credentials')
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="mb-2 text-3xl font-semibold">Athena AI Terminal</h1>
      <p className="mb-8 text-slate-400">Sign in to your trading dashboard</p>

      <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <input
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          placeholder="Username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
        <input
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          className="w-full rounded-lg bg-emerald-600 px-4 py-2 font-medium hover:bg-emerald-500"
        >
          Login
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-400">
        No account? <Link className="text-emerald-400" to="/register">Register</Link>
      </p>
    </div>
  )
}
