import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Upload" },
  { to: "/runs", label: "Ingestion Runs" },
  { to: "/review", label: "Review Dashboard" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-6">          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              Breathe ESG Ingestion Review
            </h1>
            <p className="text-sm text-slate-500">
              Normalize source data, review warnings, and lock approved rows.
            </p>
          </div>

          <nav className="flex w-full gap-2 overflow-x-auto md:w-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-4 py-2 text-sm font-medium ${
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 md:px-6">
        <Outlet />
      </main>
    </div>
  );
}