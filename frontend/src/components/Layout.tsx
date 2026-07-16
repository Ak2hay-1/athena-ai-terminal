import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  ['Dashboard', '/'],
  ['Market', '/market'],
  ['Recommendations', '/recommendations'],
  ['News', '/news'],
  ['Trading', '/trading'],
]

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-lg font-semibold">Athena AI Terminal</p>
            <p className="text-xs text-slate-400">{user?.full_name ?? user?.username}</p>
          </div>
          <nav className="flex flex-wrap gap-4 text-sm">
            {links.map(([label, path]) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({ isActive }) =>
                  isActive ? 'text-emerald-400' : 'text-slate-300 hover:text-white'
                }
              >
                {label}
              </NavLink>
            ))}
            <button onClick={logout} className="text-slate-400 hover:text-white">
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
