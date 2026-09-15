"use client";

import { useState } from "react";
import { useAuth } from "@/providers/AuthProvider";
import {
  Loader2,
  Mail,
  Lock,
  User,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Eye,
  EyeOff,
} from "lucide-react";

type Mode = "login" | "register";

export function AuthPanel({
  initialMode = "register",
}: {
  initialMode?: Mode;
}) {
  const { login, register } = useAuth();

  const [mode, setMode] = useState<Mode>(initialMode);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isLogin = mode === "login";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setError(null);
    setSuccess(null);

    // -----------------------------
    // Validation
    // -----------------------------

    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }

    if (!isLogin && !fullName.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      // -----------------------------
      // Login
      // -----------------------------

      if (isLogin) {
        await login(email, password);

        return;
      }

      // -----------------------------
      // Registration
      // -----------------------------

      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
      });

      setSuccess("Account created. You can now sign in.");

      // Clear registration fields
      setFullName("");
      setEmail("");
      setPassword("");

      // Automatically switch to login
      setMode("login");
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          isLogin
            ? "Login failed. Please try again."
            : "Registration failed. Please try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Logo mark */}
      <div className="flex items-center justify-center mb-7">
        <div className="relative w-12 h-12 rounded-2xl gradient-ai flex items-center justify-center shadow-glow">
          <Sparkles
            className="w-6 h-6 text-white"
            strokeWidth={2.2}
          />

          <div className="absolute inset-0 rounded-2xl bg-indigo-500/30 blur-lg -z-10" />
        </div>
      </div>

      {/* Heading */}
      <h2 className="text-2xl font-bold text-slate-100 text-center mb-1.5">
        {isLogin ? "Welcome back" : "Create your account"}
      </h2>

      <p className="text-sm text-slate-400 text-center mb-7">
        {isLogin ? (
          <>
            Sign in to your{" "}
            <span className="font-serif-display italic text-slate-300">
              research workspace
            </span>
            .
          </>
        ) : (
          <>
            Start{" "}
            <span className="font-serif-display italic text-slate-300">
              discovering
            </span>{" "}
            and analyzing research papers.
          </>
        )}
      </p>

      {/* Toggle */}
      <div className="flex p-1 mb-6 rounded-xl glass border border-white/10">
        <button
          type="button"
          onClick={() => {
            setMode("register");
            setError(null);
            setSuccess(null);
          }}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
            mode === "register"
              ? "bg-white/10 text-slate-100 shadow-soft"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          Register
        </button>

        <button
          type="button"
          onClick={() => {
            setMode("login");
            setError(null);
            setSuccess(null);
          }}
          className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${
            mode === "login"
              ? "bg-white/10 text-slate-100 shadow-soft"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          Sign In
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full name - registration only */}
        {!isLogin && (
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide">
              Full Name
            </label>

            <div className="relative group">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />

              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
                autoComplete="name"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400/40 focus:bg-white/[0.05] transition-all"
              />
            </div>
          </div>
        )}

        {/* Email */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide">
            Email
          </label>

          <div className="relative group">
            <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />

            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="researcher@university.edu"
              autoComplete="email"
              className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400/40 focus:bg-white/[0.05] transition-all"
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wide">
            Password
          </label>

          <div className="relative group">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />

            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete={isLogin ? "current-password" : "new-password"}
              className="w-full pl-11 pr-11 py-3 rounded-xl bg-white/[0.03] border border-white/10 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-400/40 focus:bg-white/[0.05] transition-all"
            />

            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              aria-label={
                showPassword ? "Hide password" : "Show password"
              }
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-300 animate-fade-up">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />

            <span>{error}</span>
          </div>
        )}

        {/* Success */}
        {success && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-300 animate-fade-up">
            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />

            <span>{success}</span>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="shimmer w-full py-3.5 rounded-xl gradient-ai text-white text-sm font-semibold shadow-glow hover:shadow-glow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2"
        >
          {loading && (
            <Loader2 className="w-4 h-4 animate-spin" />
          )}

          {isLogin ? "Sign In" : "Create Account"}
        </button>

        {/* Divider */}
        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10" />
          </div>

          <div className="relative flex justify-center">
            <span className="px-3 text-xs text-slate-600 bg-[#0a0f1f]">
              or continue with
            </span>
          </div>
        </div>

        {/* Social buttons */}
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            className="py-2.5 rounded-xl glass text-sm font-medium text-slate-300 hover:bg-white/10 transition-all flex items-center justify-center gap-2"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
            >
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />

              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />

              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />

              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>

            Google
          </button>

          <button
            type="button"
            className="py-2.5 rounded-xl glass text-sm font-medium text-slate-300 hover:bg-white/10 transition-all flex items-center justify-center gap-2"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.5.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.89 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10.01 10.01 0 0022 12c0-5.52-4.48-10-10-10z" />
            </svg>

            GitHub
          </button>
        </div>
      </form>

      <p className="text-xs text-slate-600 text-center mt-6 leading-relaxed">
        By continuing, you agree to the Terms of Service and Privacy Policy.
      </p>
    </div>
  );
}