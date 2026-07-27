export default function LoginPage() {
  return (
    <div className="mx-auto max-w-md px-6 py-24">
      <div className="glass-shell-outer">
        <div className="glass-shell-inner p-8">
          <h1 className="text-lg font-semibold mb-6 text-center" style={{ color: "var(--color-text-primary)" }}>
            Sign In
          </h1>
          <div className="flex flex-col gap-4">
            <input className="input" placeholder="Email" type="email" />
            <input className="input" placeholder="Password" type="password" />
            <button className="accent-button w-full justify-center">
              <span>Sign In</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
