
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Satellite, 
  MessageSquare, 
  Database, 
  Globe, 
  ArrowRight,
  Zap,
  Shield,
  Clock
} from 'lucide-react';

const Index = () => {
  const navigate = useNavigate();

  const handleStartQuery = () => {
    // Smooth scroll to chat interface by navigating to query page
    navigate('/query');
  };

  const features = [
    {
      icon: MessageSquare,
      title: 'Intelligent Querying',
      description: 'Natural language interface for satellite data exploration',
      color: 'text-primary'
    },
    {
      icon: Database,
      title: 'Comprehensive Catalog',
      description: 'Access to ISRO\'s complete satellite constellation',
      color: 'text-secondary'
    },
    {
      icon: Globe,
      title: 'Global Coverage',
      description: 'Real-time Earth observation data from multiple missions',
      color: 'text-green-500'
    },
    {
      icon: Zap,
      title: 'Real-time Analysis',
      description: 'Instant processing and visualization of satellite data',
      color: 'text-blue-500'
    },
    {
      icon: Shield,
      title: 'Secure Access',
      description: 'Government-grade security for sensitive data',
      color: 'text-purple-500'
    },
    {
      icon: Clock,
      title: '24/7 Monitoring',
      description: 'Continuous surveillance and data collection',
      color: 'text-orange-500'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="relative w-80 h-80 mx-auto flex items-center justify-center mb-6">
            {/* Center logo */}
            <div className="w-24 h-24 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center z-10 relative">
              <Satellite className="h-12 w-12 text-white" />
            </div>
            <div className="absolute w-24 h-24 bg-primary/20 rounded-full animate-ping" />
            {/* Orbiting satellites */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <Satellite className="h-5 w-5 text-primary orbit-sm" style={{ animationDelay: '0s' }} />
            </div>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <Satellite className="h-4 w-4 text-secondary/80 orbit-md" style={{ animationDelay: '-6s' }} />
            </div>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <Satellite className="h-3 w-3 text-primary/60 orbit-lg" style={{ animationDelay: '-14s' }} />
            </div>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              SatSage
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Intelligent satellite data query system powered by ISRO's Earth observation constellation. 
            Ask questions, get insights, explore our planet.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="text-lg px-8 py-3 animate-pulse hover:animate-none transition-all duration-300"
              style={{ backgroundColor: '#FF9933', color: 'white' }}
              onClick={handleStartQuery}
            >
              Start Query
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              className="text-lg px-8 py-3"
              onClick={() => navigate('/catalog')}
            >
              Explore Satellites
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <Card key={index} className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
              <CardHeader>
                <div className={`w-12 h-12 rounded-lg bg-background flex items-center justify-center mb-4 group-hover:scale-110 transition-transform ${feature.color}`}>
                  <feature.icon className="h-6 w-6" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stats Section */}
        <Card className="bg-gradient-to-r from-primary/10 to-secondary/10 border-0 mb-16">
          <CardContent className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-primary mb-2">24+</div>
                <div className="text-sm text-muted-foreground">Active Satellites</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-secondary mb-2">94.2%</div>
                <div className="text-sm text-muted-foreground">Earth Coverage</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-500 mb-2">2.4M+</div>
                <div className="text-sm text-muted-foreground">Data Points Daily</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-500 mb-2">24/7</div>
                <div className="text-sm text-muted-foreground">Monitoring</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* CTA Section */}
        <Card className="bg-gradient-to-r from-primary to-secondary text-white border-0">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Explore Earth from Space?</h2>
            <p className="text-xl opacity-90 mb-6">
              Join researchers, scientists, and analysts using ISRO's satellite data
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="bg-white text-primary hover:bg-white/90"
                onClick={handleStartQuery}
              >
                Start Your First Query
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-white text-white hover:bg-white/10"
              >
                View Documentation
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
