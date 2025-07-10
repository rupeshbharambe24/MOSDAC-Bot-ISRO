
export interface Satellite {
  id: string;
  name: string;
  type: 'observation' | 'communication' | 'navigation' | 'weather';
  status: 'active' | 'inactive' | 'maintenance';
  launchDate: string;
  mission: string;
  orbit: {
    type: 'LEO' | 'MEO' | 'GEO';
    altitude: number;
    inclination: number;
  };
  instruments: string[];
  dataTypes: string[];
  coverage: {
    region: string;
    temporal: string;
    spatial: string;
  };
}

export interface QueryTemplate {
  id: string;
  title: string;
  description: string;
  query: string;
  category: 'oceanography' | 'meteorology' | 'land' | 'atmosphere';
  icon: string;
}

export interface QueryResponse {
  id: string;
  query: string;
  timestamp: string;
  response: {
    text: string;
    data?: any[];
    visualizations?: {
      type: 'chart' | 'map' | 'table';
      data: any;
    }[];
    sources: {
      satellite: string;
      dataset: string;
      timeRange: string;
    }[];
  };
  status: 'processing' | 'completed' | 'error';
}

export interface DataStats {
  totalSatellites: number;
  activeMissions: number;
  dataPoints: string;
  coverage: string;
  lastUpdated: string;
}
