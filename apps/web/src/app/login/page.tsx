"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@ai-dev.os");
  const [password, setPassword] = useState("password123");
  const [isRegister, setIsRegister] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const handleAuthSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/dashboard");
  };

  const handleResetSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResetMessage(`Password reset instruction sent to ${forgotEmail || email}.`);
    setTimeout(() => {
      setShowForgotModal(false);
      setResetMessage(null);
    }, 2000);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black p-4">
      <div className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-950 p-8 shadow-2xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-neutral-900 text-white border border-neutral-800">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Developer OS</h1>
          <p className="text-xs text-neutral-400 mt-2">
            {isRegister ? "Create developer workspace account" : "Sign in to your autonomous workspace"}
          </p>
        </div>

        <form onSubmit={handleAuthSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-300 uppercase tracking-wider" htmlFor="email">
              Work Email
            </label>
            <input 
              id="email"
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-3.5 py-2.5 text-sm text-white placeholder-neutral-500 focus:border-neutral-500 focus:outline-none transition-colors" 
              placeholder="developer@example.com"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-300 uppercase tracking-wider" htmlFor="password">
              Password
            </label>
            <input 
              id="password"
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-3.5 py-2.5 text-sm text-white placeholder-neutral-500 focus:border-neutral-500 focus:outline-none transition-colors" 
              placeholder="••••••••"
              required
            />
          </div>
          <div className="pt-2 space-y-2">
            <button 
              type="submit"
              className="flex w-full items-center justify-center rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-black transition-all hover:bg-neutral-200 shadow-sm"
            >
              {isRegister ? "Create Workspace Account" : "Sign In & Open OS"}
            </button>
            <button 
              type="button"
              onClick={() => router.push("/dashboard")}
              className="flex w-full items-center justify-center rounded-lg bg-neutral-900 px-4 py-2 text-xs font-medium text-neutral-300 hover:text-white hover:bg-neutral-850 transition-colors border border-neutral-800"
            >
              Demo Quick Access (Bypass Auth)
            </button>
          </div>
        </form>
        
        <div className="mt-6 flex items-center justify-between text-xs text-neutral-400">
          <button 
            type="button"
            onClick={() => setShowForgotModal(true)} 
            className="hover:text-white transition-colors"
          >
            Forgot password?
          </button>
          <button 
            type="button"
            onClick={() => setIsRegister(!isRegister)} 
            className="hover:text-white transition-colors"
          >
            {isRegister ? "Already have account?" : "Create account"}
          </button>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-950 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <h3 className="text-sm font-bold text-white">Reset Account Password</h3>
              <button onClick={() => setShowForgotModal(false)} className="text-neutral-400 hover:text-white text-xs">✕</button>
            </div>
            {resetMessage ? (
              <div className="p-3 rounded-lg bg-neutral-900 border border-neutral-800 text-neutral-200 text-xs">
                {resetMessage}
              </div>
            ) : (
              <form onSubmit={handleResetSubmit} className="space-y-4">
                <div>
                  <label className="text-xs text-neutral-300 block mb-1">Enter your email</label>
                  <input 
                    type="email" 
                    value={forgotEmail || email}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    className="w-full bg-neutral-900 border border-neutral-800 rounded-lg p-2.5 text-sm text-white placeholder-neutral-500 focus:border-neutral-500 focus:outline-none"
                    required
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button type="button" onClick={() => setShowForgotModal(false)} className="px-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-neutral-300 hover:bg-neutral-850 hover:text-white">Cancel</button>
                  <button type="submit" className="px-4 py-2 rounded-lg bg-white text-xs font-semibold text-black hover:bg-neutral-200 shadow-sm">Send Reset Link</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
