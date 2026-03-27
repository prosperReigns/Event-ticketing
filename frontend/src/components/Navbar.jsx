import { NavLink } from "react-router-dom";

const Navbar = () => {
  const linkBase =
    "rounded-full px-4 py-2 text-sm font-semibold transition hover:bg-white";

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-lg font-semibold text-slate-900">
            Event Guest Check-in
          </p>
          <p className="text-xs text-slate-500">QR-powered staff console</p>
        </div>
        <nav className="flex items-center gap-2 rounded-full bg-slate-100 p-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `${linkBase} ${
                isActive ? "bg-white text-slate-900 shadow" : "text-slate-600"
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/checkin"
            className={({ isActive }) =>
              `${linkBase} ${
                isActive ? "bg-white text-slate-900 shadow" : "text-slate-600"
              }`
            }
          >
            Check-In
          </NavLink>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
