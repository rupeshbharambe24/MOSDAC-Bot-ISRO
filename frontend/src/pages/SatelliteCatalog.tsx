import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Search,
  Filter,
  Satellite,
  Activity,
  Eye,
  Download,
  Loader2,
} from 'lucide-react';

interface CatalogSatellite {
  name: string;
  instruments: string[];
  products: string[];
  source?: string;
}

const FALLBACK_SATELLITES: CatalogSatellite[] = [
  { name: 'OCEANSAT-3', instruments: ['Ocean Color Monitor', 'Thermal IR'], products: ['SST', 'Chlorophyll', 'Ocean Color'] },
  { name: 'RESOURCESAT-2A', instruments: ['LISS-3', 'LISS-4', 'AWIFS'], products: ['Land Use', 'Vegetation Index'] },
  { name: 'CARTOSAT-3', instruments: ['Panchromatic Camera', 'Multispectral Camera'], products: ['High Resolution Imagery'] },
  { name: 'INSAT-3D', instruments: ['VHRR', 'SAPHIR', 'IMAGER'], products: ['Sea Surface Temperature', 'TPW', 'OLR'] },
  { name: 'INSAT-3DR', instruments: ['VHRR', 'SAPHIR'], products: ['Rainfall', 'Humidity', 'Wind Speed'] },
  { name: 'SCATSAT-1', instruments: ['SCAT'], products: ['Ocean Wind Vectors', 'Wind Speed'] },
  { name: 'Megha-Tropiques', instruments: ['SAPHIR', 'MADRAS'], products: ['TPW', 'Rainfall'] },
  { name: 'SARAL', instruments: ['AltiKa'], products: ['Sea Surface Height', 'Significant Wave Height'] },
];

const SatelliteCatalog: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [satellites, setSatellites] = useState<CatalogSatellite[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    const fetchSatellites = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/satellites');
        if (res.ok) {
          const data = await res.json();
          if (data.satellites && data.satellites.length > 0) {
            setSatellites(data.satellites);
            setIsLive(true);
          } else {
            setSatellites(FALLBACK_SATELLITES);
          }
        } else {
          setSatellites(FALLBACK_SATELLITES);
        }
      } catch {
        setSatellites(FALLBACK_SATELLITES);
      } finally {
        setLoading(false);
      }
    };
    fetchSatellites();
  }, []);

  const filteredSatellites = satellites.filter(sat => {
    const matchesSearch =
      sat.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sat.instruments.some(i => i.toLowerCase().includes(searchTerm.toLowerCase())) ||
      sat.products.some(p => p.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = typeFilter === 'all' || (
      typeFilter === 'ocean' ? sat.products.some(p => /sea|ocean|wave|wind/i.test(p)) :
      typeFilter === 'weather' ? sat.products.some(p => /rain|humidity|cyclone|tpw|olr/i.test(p)) :
      typeFilter === 'land' ? sat.products.some(p => /land|vegetation|imagery/i.test(p)) :
      true
    );
    return matchesSearch && matchesType;
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
          <Skeleton className="h-10 w-36" />
        </div>
        <Card><CardContent className="p-4"><Skeleton className="h-10 w-full" /></CardContent></Card>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div>
                    <Skeleton className="h-5 w-28 mb-1" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Skeleton className="h-3 w-20 mb-2" />
                  <div className="flex gap-1">
                    <Skeleton className="h-5 w-16 rounded-full" />
                    <Skeleton className="h-5 w-20 rounded-full" />
                  </div>
                </div>
                <Skeleton className="h-16 w-full rounded-lg" />
                <div className="flex gap-2">
                  <Skeleton className="h-8 flex-1" />
                  <Skeleton className="h-8 flex-1" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Satellite Catalog</h1>
          <p className="text-muted-foreground">
            {isLive ? 'Live data from Knowledge Graph' : 'Sample satellite data'} — {satellites.length} satellites
          </p>
        </div>
        <Button className="gradient-primary text-white" onClick={() => {
          const blob = new Blob([JSON.stringify(satellites, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'isro-satellite-catalog.json';
          a.click();
          URL.revokeObjectURL(url);
        }}>
          <Download className="h-4 w-4 mr-2" />
          Export Catalog
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search satellites, instruments, products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="ocean">Ocean</SelectItem>
                <SelectItem value="weather">Weather</SelectItem>
                <SelectItem value="land">Land</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {filteredSatellites.length} of {satellites.length} satellites
        </p>
        {(searchTerm || typeFilter !== 'all') && (
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filters applied</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSatellites.map((sat, idx) => (
          <Card key={idx} className="group hover:shadow-lg transition-all duration-300">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                    <Satellite className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{sat.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {sat.instruments.length} instrument{sat.instruments.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                {isLive && (
                  <Badge className="bg-green-500/10 text-green-500 border-green-500/20">Live</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-2">Instruments</h4>
                <div className="flex flex-wrap gap-1">
                  {sat.instruments.slice(0, 3).map((instrument, i) => (
                    <Badge key={i} variant="outline" className="text-xs">{instrument}</Badge>
                  ))}
                  {sat.instruments.length > 3 && (
                    <Badge variant="outline" className="text-xs">+{sat.instruments.length - 3} more</Badge>
                  )}
                  {sat.instruments.length === 0 && (
                    <span className="text-xs text-muted-foreground">No instruments listed</span>
                  )}
                </div>
              </div>

              <div className="bg-primary/5 rounded-lg p-3">
                <h4 className="text-sm font-medium mb-2">Data Products</h4>
                <div className="flex flex-wrap gap-1">
                  {sat.products.slice(0, 3).map((product, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{product}</Badge>
                  ))}
                  {sat.products.length > 3 && (
                    <Badge variant="secondary" className="text-xs">+{sat.products.length - 3} more</Badge>
                  )}
                  {sat.products.length === 0 && (
                    <span className="text-xs text-muted-foreground">No products listed</span>
                  )}
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline" size="sm" className="flex-1"
                  onClick={() => navigate('/query', { state: { initialQuery: `Tell me about ${sat.name} satellite and its instruments` } })}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  Ask About
                </Button>
                <Button
                  variant="outline" size="sm" className="flex-1"
                  onClick={() => window.open('https://mosdac.gov.in', '_blank')}
                >
                  <Activity className="h-3 w-3 mr-1" />
                  MOSDAC
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredSatellites.length === 0 && (
        <Card className="p-8">
          <div className="text-center space-y-4">
            <Satellite className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-medium">No satellites found</h3>
              <p className="text-muted-foreground">Try adjusting your search or filter criteria</p>
            </div>
            <Button variant="outline" onClick={() => { setSearchTerm(''); setTypeFilter('all'); }}>
              Clear Filters
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SatelliteCatalog;
