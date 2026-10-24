import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';

export default function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [mapStatus, setMapStatus] = useState('Checking map configuration…');
  const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN?.trim();

  useEffect(() => {
    if (!token) {
      setMapStatus('Mapbox token is not configured. Add VITE_MAPBOX_ACCESS_TOKEN to frontend/.env to enable the basemap.');
      return undefined;
    }
    mapboxgl.accessToken = token;
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [20, 20],
      zoom: 1.2,
      attributionControl: true,
    });
    mapRef.current = map;
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.on('load', () => setMapStatus('Basemap loaded. Satellite event layers will be added in a later integration task.'));
    map.on('error', () => setMapStatus('Map could not load. Check token permissions and network connection.'));
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [token]);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark">✳</div>
        <div><strong>PyroScope</strong><span>Wildfire event intelligence</span></div>
        <span className="status">FRONTEND BOILERPLATE</span>
      </header>
      <section className="intro">
        <p className="eyebrow">DIP-12 · FRONTEND FOUNDATION</p>
        <h1>Wildfire event overview</h1>
        <p className="subtitle">Mapbox GL JS scaffold ready for future MODIS/VIIRS event layers.</p>
      </section>
      <section className="map-panel">
        <div className="panel-head"><div><strong>Interactive basemap</strong><small>Mapbox GL JS · dark style</small></div><span className="tag">MAP PREVIEW</span></div>
        <div className="map-area">
          <div ref={mapContainer} className="map-container" />
          {!token && <div className="map-placeholder"><div className="placeholder-icon">⌖</div><h2>Mapbox token needed</h2><p>{mapStatus}</p><code>VITE_MAPBOX_ACCESS_TOKEN=your_public_token</code></div>}
        </div>
        <div className="map-status">{mapStatus}</div>
      </section>
      <p className="note">This is a setup scaffold, not a live wildfire monitoring system. No NASA FIRMS data or fire-event detections are loaded yet.</p>
    </main>
  );
}
