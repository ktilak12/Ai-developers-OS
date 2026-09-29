import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 p-4">
      <div className="w-full max-w-sm rounded-xl border border-neutral-800 bg-neutral-900 p-8 shadow-2xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600/20 text-blue-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></svg>
          </div>
          <h1 className="text-2xl font-bold text-white">AI Developer OS</h1>
          <p className="text-sm text-neutral-400 mt-2">Sign in to your workspace</p>
        </div>

        <form className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-300" htmlFor="email">Email</label>
            <input 
              id="email"
              type="email" 
              className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-4 py-2 text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors" 
              placeholder="developer@example.com"
              defaultValue="admin@ai-dev.os"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-neutral-300" htmlFor="password">Password</label>
            <input 
              id="password"
              type="password" 
              className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-4 py-2 text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors" 
              placeholder="••••••••"
              defaultValue="password123"
            />
          </div>
          <div className="pt-2">
            <Link 
              href="/dashboard"
              className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Sign In
            </Link>
          </div>
        </form>
        
        <div className="mt-6 flex items-center justify-between text-sm text-neutral-400">
          <Link href="#" className="hover:text-white transition-colors">Forgot password?</Link>
          <Link href="#" className="hover:text-white transition-colors">Create account</Link>
        </div>
      </div>
    </div>
  );
}
