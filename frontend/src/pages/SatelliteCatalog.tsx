
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search, 
  Filter, 
  Satellite, 
  Calendar, 
  Globe,
  Activity,
  Eye,
  Download
} from 'lucide-react';
import { Satellite as SatelliteType } from '@/types/satellite';

const SatelliteCatalog: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const satellites: SatelliteType[] = [
    {
      id: '1',
      name: 'OCEANSAT-3',
      type: 'observation',
      status: 'active',
      launchDate: '2021-11-26',
      mission: 'Ocean Color Monitor',
      orbit: {
        type: 'LEO',
        altitude: 817,
        inclination: 98.1
      },
      instruments: ['Ocean Color Monitor', 'Thermal Infrared Imaging Satellite'],
      dataTypes: ['Sea Surface Temperature', 'Chlorophyll Concentration', 'Ocean Color'],
      coverage: {
        region: 'Global',
        temporal: 'Daily',
        spatial: '1km'
      }
    },
    {
      id: '2',
      name: 'RESOURCESAT-2A',
      type: 'observation',
      status: 'active',
      launchDate: '2016-12-07',
      mission: 'Land Resources Management',
      orbit: {
        type: 'LEO',
        altitude: 817,
        inclination: 98.69
      },
      instruments: ['LISS-3', 'LISS-4', 'AWIFS'],
      dataTypes: ['Land Use', 'Vegetation Index', 'Agricultural Monitoring'],
      coverage: {
        region: 'India and surrounding regions',
        temporal: '24 days',
        spatial: '5.8m to 56m'
      }
    },
    {
      id: '3',
      name: 'CARTOSAT-3',
      type: 'observation',
      status: 'maintenance',
      launchDate: '2019-11-27',
      mission: 'High Resolution Imaging',
      orbit: {
        type: 'LEO',
        altitude: 509,
        inclination: 97.5
      },
      instruments: ['Panchromatic Camera', 'Multispectral Camera'],
      dataTypes: ['High Resolution Imagery', 'Cartographic Applications'],
      coverage: {
        region: 'Global',
        temporal: '4 days',
        spatial: '0.25m'
      }
    }
  ];

  const filteredSatellites = satellites.filter(satellite => {
    const matchesSearch = satellite.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         satellite.mission.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || satellite.status === statusFilter;
    const matchesType = typeFilter === 'all' || satellite.type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'maintenance':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'inactive':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Satellite Catalog</h1>
          <p className="text-muted-foreground">Browse and explore ISRO's satellite constellation</p>
        </div>
        <Button className="gradient-primary text-white">
          <Download className="h-4 w-4 mr-2" />
          Export Catalog
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search satellites, missions, instruments..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="maintenance">Maintenance</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="observation">Observation</SelectItem>
                <SelectItem value="communication">Communication</SelectItem>
                <SelectItem value="navigation">Navigation</SelectItem>
                <SelectItem value="weather">Weather</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {filteredSatellites.length} of {satellites.length} satellites
        </p>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Filters applied</span>
        </div>
      </div>

      {/* Satellite Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSatellites.map((satellite) => (
          <Card key={satellite.id} className="group hover:shadow-lg transition-all duration-300 cursor-pointer">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                    <Satellite className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{satellite.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{satellite.mission}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(satellite.status)}>
                  {satellite.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>{new Date(satellite.launchDate).getFullYear()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <span>{satellite.orbit.type}</span>
                </div>
              </div>

              {/* Orbit Details */}
              <div className="bg-muted/30 rounded-lg p-3">
                <h4 className="text-sm font-medium mb-2">Orbital Parameters</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-muted-foreground">Altitude:</span>
                    <span className="ml-1 font-medium">{satellite.orbit.altitude} km</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Inclination:</span>
                    <span className="ml-1 font-medium">{satellite.orbit.inclination}°</span>
                  </div>
                </div>
              </div>

              {/* Instruments */}
              <div>
                <h4 className="text-sm font-medium mb-2">Instruments</h4>
                <div className="flex flex-wrap gap-1">
                  {satellite.instruments.slice(0, 2).map((instrument, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {instrument}
                    </Badge>
                  ))}
                  {satellite.instruments.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{satellite.instruments.length - 2} more
                    </Badge>
                  )}
                </div>
              </div>

              {/* Coverage */}
              <div className="bg-primary/5 rounded-lg p-3">
                <h4 className="text-sm font-medium mb-2">Coverage</h4>
                <div className="space-y-1 text-xs">
                  <div>
                    <span className="text-muted-foreground">Spatial:</span>
                    <span className="ml-1 font-medium">{satellite.coverage.spatial}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Temporal:</span>
                    <span className="ml-1 font-medium">{satellite.coverage.temporal}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Eye className="h-3 w-3 mr-1" />
                  View Details
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  <Activity className="h-3 w-3 mr-1" />
                  Live Data
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredSatellites.length === 0 && (
        <Card className="p-8">
          <div className="text-center space-y-4">
            <Satellite className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-medium">No satellites found</h3>
              <p className="text-muted-foreground">Try adjusting your search or filter criteria</p>
            </div>
            <Button variant="outline" onClick={() => {
              setSearchTerm('');
              setStatusFilter('all');
              setTypeFilter('all');
            }}>
              Clear Filters
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SatelliteCatalog;
