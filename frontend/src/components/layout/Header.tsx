
import React from 'react';
import { Satellite, Moon, Sun, Menu, Search, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface HeaderProps {
  onToggleSidebar: () => void;
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, isDarkMode, onToggleTheme }) => {
  return (
    <header className="h-16 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 sticky top-0 z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <div className="flex items-center gap-3">
            <div className="relative">
              <Satellite className="h-8 w-8 text-primary satellite-orbit" />
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                ISRO SatQuery
              </h1>
              <p className="text-xs text-muted-foreground">Satellite Data Intelligence</p>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search satellites, data, missions..."
              className="pl-10 bg-muted/50"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-secondary rounded-full text-xs flex items-center justify-center text-black">
              2
            </span>
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
          >
            {isDarkMode ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          <div className="hidden sm:flex items-center gap-2 ml-4 pl-4 border-l">
            <div className="h-8 w-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white text-sm font-bold">
              IS
            </div>
            <span className="text-sm font-medium">ISRO Portal</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
