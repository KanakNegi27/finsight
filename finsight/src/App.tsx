
import "./App.css";
import { AuthProvider } from "./AuthProvider";
import { useAuth } from "./auth";
import { Login } from "./Login";
import { Dashboard } from "./Dashboard";

function Gate() {
  const { user, initializing } = useAuth();

  if (initializing) {
    return (
      <div className="splash">
        <span className="brand-mark large">₹</span>
        <p>Loading FinSight…</p>
      </div>
    );
  }

  return user ? <Dashboard /> : <Login />;
}

function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}

export default App;
