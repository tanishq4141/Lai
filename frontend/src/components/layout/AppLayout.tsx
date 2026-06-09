import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  GitCompareArrows,
  Scale,
  FileText,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Upload', icon: Upload },
  { to: '/compare', label: 'Compare', icon: GitCompareArrows },
];

export function AppLayout() {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-[var(--color-background)]">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[var(--color-border)] bg-[var(--color-card)] flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-6 border-b border-[var(--color-border)]">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-[var(--color-primary)] flex items-center justify-center group-hover:animate-pulse-glow transition-all">
              <Scale className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-[var(--color-foreground)]">Lai</span>
              <p className="text-[10px] text-[var(--color-muted-foreground)] leading-tight">
                Legal Document Intelligence
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
            Menu
          </p>
          {navItems.map((item) => {
            const isActive =
              item.to === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/20'
                    : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-[var(--color-secondary)]',
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--color-border)]">
          <div className="flex items-center gap-2 text-[var(--color-muted-foreground)]">
            <FileText className="h-3.5 w-3.5" />
            <span className="text-xs">v0.1.0</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
