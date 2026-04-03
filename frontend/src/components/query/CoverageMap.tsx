import React, { useEffect, useRef, useMemo, useState } from 'react';
import L, { LatLngBoundsExpression } from 'leaflet';

export interface Region {
  name: string;
  bounds: [[number, number], [number, number]];
  color: string;
}

const REGION_REGISTRY: Array<{ patterns: string[]; region: Region }> = [
  {
    patterns: ['indian ocean'],
    region: { name: 'Indian Ocean', bounds: [[-60, 20], [30, 120]], color: '#38bdf8' },
  },
  {
    patterns: ['bay of bengal'],
    region: { name: 'Bay of Bengal', bounds: [[5, 80], [22, 100]], color: '#34d399' },
  },
  {
    patterns: ['arabian sea'],
    region: { name: 'Arabian Sea', bounds: [[5, 55], [25, 78]], color: '#a78bfa' },
  },
  {
    patterns: ['india', 'indian subcontinent', 'indian region', 'indian mainland'],
    region: { name: 'India / Indian Subcontinent', bounds: [[8, 68], [37, 97]], color: '#fbbf24' },
  },
  {
    patterns: ['himalaya', 'himalayan'],
    region: { name: 'Himalayan Region', bounds: [[27, 70], [37, 97]], color: '#f472b6' },
  },
  {
    patterns: ['north india'],
    region: { name: 'North India', bounds: [[22, 68], [37, 78]], color: '#fb923c' },
  },
  {
    patterns: ['south asia'],
    region: { name: 'South Asia', bounds: [[5, 60], [40, 100]], color: '#e879f9' },
  },
  {
    patterns: ['tropical', 'tropics'],
    region: { name: 'Tropical Region', bounds: [[-30, 30], [30, 120]], color: '#86efac' },
  },
  {
    patterns: ['global ocean', 'global'],
    region: { name: 'Global Ocean', bounds: [[-60, -180], [60, 180]], color: '#60a5fa' },
  },
  {
    patterns: ['kerala'],
    region: { name: 'Kerala', bounds: [[8.3, 74.9], [12.8, 77.4]], color: '#2dd4bf' },
  },
  {
    patterns: ['gujarat'],
    region: { name: 'Gujarat', bounds: [[20.1, 68.2], [24.7, 74.4]], color: '#f87171' },
  },
  {
    patterns: ['eastern india'],
    region: { name: 'Eastern India', bounds: [[20, 80], [27, 97]], color: '#c084fc' },
  },
  {
    patterns: ['southern ocean'],
    region: { name: 'Southern Ocean', bounds: [[-60, 20], [-40, 120]], color: '#22d3ee' },
  },
  {
    patterns: ['coastal', 'coast'],
    region: { name: 'Indian Coastal Region', bounds: [[6, 68], [23, 88]], color: '#fb923c' },
  },
];

export function detectRegions(text: string): Region[] {
  const lower = text.toLowerCase();
  const seen = new Set<string>();
  const found: Region[] = [];
  for (const entry of REGION_REGISTRY) {
    if (entry.patterns.some(p => lower.includes(p))) {
      if (!seen.has(entry.region.name)) {
        seen.add(entry.region.name);
        found.push(entry.region);
      }
    }
  }
  return found;
}

type MapStyle = 'dark' | 'satellite' | 'light';

const TILE_LAYERS: Record<MapStyle, { url: string; attribution: string }> = {
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP',
  },
  light: {
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
};

interface CoverageMapProps {
  regions: Region[];
}

const CoverageMap: React.FC<CoverageMapProps> = ({ regions }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const [activeStyle, setActiveStyle] = useState<MapStyle>('dark');

  const center = useMemo<[number, number]>(() => {
    if (regions.length === 0) return [15, 80];
    const lats = regions.map(r => (r.bounds[0][0] + r.bounds[1][0]) / 2);
    const lngs = regions.map(r => (r.bounds[0][1] + r.bounds[1][1]) / 2);
    return [
      lats.reduce((a, b) => a + b, 0) / lats.length,
      lngs.reduce((a, b) => a + b, 0) / lngs.length,
    ];
  }, [regions]);

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current) return;
    if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; }

    const map = L.map(containerRef.current, { scrollWheelZoom: false, zoomControl: true }).setView(center, 3);
    mapRef.current = map;

    const tile = TILE_LAYERS.dark;
    tileLayerRef.current = L.tileLayer(tile.url, { attribution: tile.attribution }).addTo(map);

    regions.forEach(region => {
      L.rectangle(region.bounds as LatLngBoundsExpression, {
        color: region.color,
        fillColor: region.color,
        fillOpacity: 0.2,
        weight: 2,
        dashArray: '4 4',
      })
        .bindTooltip(`<strong>${region.name}</strong>`, { sticky: true, className: 'leaflet-region-tooltip' })
        .addTo(map);
    });

    return () => { map.remove(); mapRef.current = null; };
  }, [regions, center]);

  // Swap tile layer when style changes
  useEffect(() => {
    if (!mapRef.current) return;
    if (tileLayerRef.current) { tileLayerRef.current.remove(); }
    const tile = TILE_LAYERS[activeStyle];
    tileLayerRef.current = L.tileLayer(tile.url, { attribution: tile.attribution }).addTo(mapRef.current);
  }, [activeStyle]);

  const styleButtons: { key: MapStyle; label: string }[] = [
    { key: 'dark', label: 'Dark' },
    { key: 'satellite', label: 'Satellite' },
    { key: 'light', label: 'Light' },
  ];

  return (
    <div style={{ borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
      {/* Style switcher */}
      <div style={{
        display: 'flex', gap: '4px', padding: '6px 8px',
        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
      }}>
        {styleButtons.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveStyle(key)}
            style={{
              fontSize: '11px', padding: '2px 10px', borderRadius: '4px', border: 'none',
              cursor: 'pointer',
              background: activeStyle === key ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.15)',
              color: activeStyle === key ? '#000' : '#fff',
              fontWeight: activeStyle === key ? 600 : 400,
              transition: 'all 0.15s',
            }}
          >
            {label}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'rgba(255,255,255,0.5)', alignSelf: 'center' }}>
          {regions.map(r => r.name).join(' · ')}
        </span>
      </div>

      {/* Map */}
      <div ref={containerRef} style={{ height: '300px', width: '100%' }} />
    </div>
  );
};

export default CoverageMap;
