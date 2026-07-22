import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/client'

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
  })
  const [error, setError] = useState('')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')

    try {
      await register(form)
      navigate('/login')
    } catch (err) {
      setError('Registration failed')
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="mb-8 text-3xl font-semibold">Create account</h1>

      <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        {(['username', 'email', 'full_name', 'password'] as const).map((field) => (
          <input
            key={field}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            placeholder={field.replace('_', ' ')}
            type={field === 'password' ? 'password' : 'text'}
            value={form[field]}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                [field]: event.target.value,
              }))
            }
          />
        ))}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button type="submit" className="w-full rounded-lg bg-emerald-600 px-4 py-2">
          Register
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-400">
        Already have an account? <Link className="text-emerald-400" to="/login">Login</Link>
      </p>
    </div>
  )
}
