import { useEffect, useRef, useState } from "react";

function App() {
  const hostRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let disposed = false;

    const boot = async () => {
      try {
        const response = await fetch("/legacy-panel.html", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Template yuklanmadi: HTTP ${response.status}`);
        }
        const html = await response.text();
        if (disposed || !hostRef.current) return;

        hostRef.current.innerHTML = html;

        const { initLegacyAdminPanel } = await import("./legacyAdmin.js");
        if (disposed) return;
        initLegacyAdminPanel();
        setReady(true);
      } catch (e) {
        setError(e.message || "Noma'lum xatolik");
      }
    };

    boot();

    return () => {
      disposed = true;
    };
  }, []);

  if (error) {
    return <div style={{ padding: 20 }}>Xato: {error}</div>;
  }

  return (
    <>
      {!ready && <div style={{ padding: 20 }}>Admin panel yuklanmoqda...</div>}
      <div ref={hostRef} />
    </>
  );
}

export default App;
