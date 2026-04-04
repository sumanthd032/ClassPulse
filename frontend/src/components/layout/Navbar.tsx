import { Bell, LogOut, User } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="fixed top-0 z-40 w-full border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div
          className="flex cursor-pointer items-center gap-2"
          onClick={() => navigate("/")}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-sm">
            CP
          </div>
          <span className="font-semibold text-gray-900">ClassPulse</span>
        </div>

        <div className="flex items-center gap-3">
          <button className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100">
            <Bell className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1.5">
            <User className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">{user?.full_name}</span>
            <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs text-white capitalize">
              {user?.role}
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
