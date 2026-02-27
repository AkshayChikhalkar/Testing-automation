import React, { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
  useMediaQuery,
  Button,
  Menu,
  MenuItem,
  Avatar,
  Chip,
  Fade,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  ModelTraining as ModelsIcon,
  PlayArrow as TestRunsIcon,
  Code as SimulationIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  ChevronLeft,
  ChevronRight,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import apiClient from '../../services/api';
import { AccountCircle, Logout, Lock } from '@mui/icons-material';

const drawerWidth = 280;
const collapsedDrawerWidth = 64;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [currentUser, setCurrentUser] = React.useState<{ username: string; email?: string } | null>(null);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const publicPaths = ['/login', '/signup'];
    if (!token && !publicPaths.includes(location.pathname)) {
      navigate('/login');
    }
  }, [location.pathname, navigate]);

  React.useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setCurrentUser(null);
      return;
    }
    (async () => {
      try {
        const res = await apiClient.get('/auth/me');
        setCurrentUser({ username: res.data.username, email: res.data.email });
      } catch {
        // token invalid -> force logout
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        setCurrentUser(null);
        navigate('/login');
      }
    })();
  }, [location.pathname, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    setCurrentUser(null);
    navigate('/login');
  };

  const handleMenu = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => setAnchorEl(null);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleSidebarToggle = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const menuItems = [
    { 
      text: t('navigation.dashboard'), 
      icon: <DashboardIcon />, 
      path: '/dashboard',
      color: '#1976d2',
      description: t('dashboard.overview')
    },
    { 
      text: t('navigation.models'), 
      icon: <ModelsIcon />, 
      path: '/models',
      color: '#7b1fa2',
      description: t('models.title')
    },
    { 
      text: t('navigation.testRuns'), 
      icon: <TestRunsIcon />, 
      path: '/test-runs',
      color: '#2e7d32',
      description: t('testRuns.title')
    },
    { 
      text: t('navigation.simulationRunner'), 
      icon: <SimulationIcon />, 
      path: '/simulation-runner',
      color: '#0288d1',
      description: t('simulationRunner.description')
    },
    { 
      text: t('navigation.reports'), 
      icon: <ReportsIcon />, 
      path: '/reports',
      color: '#f57c00',
      description: t('reports.title')
    },
    { 
      text: t('navigation.settings'), 
      icon: <SettingsIcon />, 
      path: '/settings',
      color: '#5d4037',
      description: t('settings.title')
    },
  ];

  const drawer = (
    <Box 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        color: 'white',
        position: 'relative',
        overflow: 'visible'
      }}
    >
      {/* Header */}
      <Box 
        sx={{ 
          p: 3,
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Fade in={!sidebarCollapsed} timeout={300}>
            <Box>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 700,
                  background: 'linear-gradient(45deg, #64b5f6, #42a5f5)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5
                }}
              >
          MATLAB Automation
        </Typography>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '0.75rem'
                }}
              >
                Testing Platform
              </Typography>
            </Box>
          </Fade>
          <IconButton
            onClick={handleSidebarToggle}
            sx={{
              color: 'white',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '50%',
              width: 28,
              height: 28,
              border: '2px solid rgba(255, 255, 255, 0.3)',
              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
              position: 'absolute',
              right: 8,
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 1000,
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                transform: 'translateY(-50%) scale(1.1)',
                boxShadow: '0 6px 16px rgba(102, 126, 234, 0.5)',
              },
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              '& .MuiSvgIcon-root': {
                fontSize: '0.9rem',
                fontWeight: 'bold'
              }
            }}
            title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight /> : <ChevronLeft />}
          </IconButton>
        </Box>
      </Box>

      {/* User Profile Section */}
      {currentUser && (
        <Box sx={{ 
          p: sidebarCollapsed ? 1 : 2, 
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: sidebarCollapsed ? 'center' : 'stretch'
        }}>
          <Box 
            display="flex" 
            alignItems="center" 
            gap={sidebarCollapsed ? 0 : 2}
            sx={{ 
              p: sidebarCollapsed ? 1 : 2,
              borderRadius: sidebarCollapsed ? '50%' : '12px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              transition: 'all 0.3s ease',
              width: sidebarCollapsed ? 48 : '100%',
              height: sidebarCollapsed ? 48 : 'auto',
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              position: 'relative'
            }}
          >
            <Avatar
              sx={{
                width: sidebarCollapsed ? 32 : 40,
                height: sidebarCollapsed ? 32 : 40,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                fontWeight: 600,
                fontSize: sidebarCollapsed ? '0.875rem' : '1rem'
              }}
            >
              {currentUser.username.charAt(0).toUpperCase()}
            </Avatar>
            <Fade in={!sidebarCollapsed} timeout={300}>
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    fontWeight: 600,
                    color: 'white',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {currentUser.username}
                </Typography>
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '0.7rem'
                  }}
                >
                  {currentUser.email || 'User'}
                </Typography>
              </Box>
            </Fade>
            {sidebarCollapsed && (
              <Tooltip 
                title={`${currentUser.username}${currentUser.email ? `\n${currentUser.email}` : ''}`}
                placement="right"
                arrow
                componentsProps={{
                  tooltip: {
                    sx: {
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      color: 'white',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                      whiteSpace: 'pre-line'
                    }
                  },
                  arrow: {
                    sx: {
                      color: 'rgba(0, 0, 0, 0.8)',
                    }
                  }
                }}
              >
                <Box />
              </Tooltip>
            )}
          </Box>
        </Box>
      )}

      {/* Navigation */}
      <Box sx={{ 
        flexGrow: 1, 
        p: sidebarCollapsed ? 1 : 1,
        overflow: 'visible',
        position: 'relative'
      }}>
        <List sx={{ 
          px: sidebarCollapsed ? 0.5 : 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: sidebarCollapsed ? 'center' : 'stretch',
          gap: sidebarCollapsed ? 0.5 : 0,
          overflow: 'visible'
        }}>
          {menuItems.map((item, index) => {
            const isSelected = location.pathname === item.path;
            const navButton = (
            <ListItemButton
                selected={isSelected}
              onClick={() => {
                navigate(item.path);
                if (isMobile) {
                  setMobileOpen(false);
                }
                }}
                sx={{
                  borderRadius: sidebarCollapsed ? '50%' : '12px',
                  py: sidebarCollapsed ? 1.5 : 1.5,
                  px: sidebarCollapsed ? 1.5 : 2,
                  mb: 0.5,
                  minWidth: sidebarCollapsed ? 48 : 'auto',
                  width: sidebarCollapsed ? 48 : 'auto',
                  height: sidebarCollapsed ? 48 : 'auto',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  alignItems: sidebarCollapsed ? 'center' : 'flex-start',
                  background: isSelected 
                    ? sidebarCollapsed 
                      ? item.color
                      : `linear-gradient(135deg, ${item.color}40, ${item.color}20)`
                    : 'transparent',
                  border: isSelected 
                    ? sidebarCollapsed
                      ? 'none'
                      : `1px solid ${item.color}60`
                    : '1px solid transparent',
                  color: isSelected ? 'white' : 'rgba(255, 255, 255, 0.8)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  overflow: 'hidden',
                  position: 'relative',
                  '&:hover': {
                    background: sidebarCollapsed
                      ? item.color
                      : `linear-gradient(135deg, ${item.color}30, ${item.color}10)`,
                    border: sidebarCollapsed
                      ? 'none'
                      : `1px solid ${item.color}40`,
                    transform: sidebarCollapsed ? 'scale(1.02)' : 'translateX(2px)',
                    color: 'white',
                    boxShadow: sidebarCollapsed 
                      ? `0 2px 8px ${item.color}30`
                      : 'none',
                  },
                  '&.Mui-selected': {
                    background: sidebarCollapsed
                      ? item.color
                      : `linear-gradient(135deg, ${item.color}50, ${item.color}30)`,
                    border: sidebarCollapsed
                      ? 'none'
                      : `1px solid ${item.color}80`,
                    color: 'white',
                    '&:hover': {
                      background: sidebarCollapsed
                        ? item.color
                        : `linear-gradient(135deg, ${item.color}60, ${item.color}40)`,
                    }
                  }
                }}
              >
                <ListItemIcon 
                  sx={{ 
                    minWidth: sidebarCollapsed ? 0 : 40,
                    width: sidebarCollapsed ? 'auto' : 40,
                    color: isSelected 
                      ? (sidebarCollapsed ? 'white' : item.color)
                      : 'rgba(255, 255, 255, 0.7)',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    '& .MuiSvgIcon-root': {
                      fontSize: sidebarCollapsed ? '1.5rem' : '1.25rem'
                    }
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <Fade in={!sidebarCollapsed} timeout={300}>
                  <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    <ListItemText 
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: isSelected ? 600 : 500,
                        fontSize: '0.9rem'
                      }}
                    />
                    {!sidebarCollapsed && (
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: 'rgba(255, 255, 255, 0.6)',
                          fontSize: '0.7rem',
                          display: 'block',
                          mt: 0.5
                        }}
                      >
                        {item.description}
                      </Typography>
                    )}
                  </Box>
                </Fade>
                {isSelected && !sidebarCollapsed && (
                  <Chip
                    label="Active"
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: '0.65rem',
                      background: item.color,
                      color: 'white',
                      fontWeight: 600
                    }}
                  />
                )}
            </ListItemButton>
            );

            return (
              <Fade in timeout={200 + index * 50} key={item.text}>
                <ListItem 
                  disablePadding 
                  sx={{ 
                    mb: 0.5,
                    borderRadius: '12px',
                    overflow: 'hidden',
                    width: sidebarCollapsed ? 'auto' : '100%',
                    display: 'flex',
                    justifyContent: sidebarCollapsed ? 'center' : 'stretch'
                  }}
                >
                  {sidebarCollapsed ? (
                    <Tooltip 
                      title={`${item.text}${isSelected ? ' (Active)' : ''}`} 
                      placement="right"
                      arrow
                      componentsProps={{
                        tooltip: {
                          sx: {
                            backgroundColor: isSelected ? item.color : 'rgba(0, 0, 0, 0.8)',
                            color: 'white',
                            fontSize: '0.875rem',
                            fontWeight: 500,
                            borderRadius: '8px',
                            boxShadow: isSelected 
                              ? `0 4px 12px ${item.color}40`
                              : '0 4px 12px rgba(0, 0, 0, 0.15)',
                          }
                        },
                        arrow: {
                          sx: {
                            color: isSelected ? item.color : 'rgba(0, 0, 0, 0.8)',
                          }
                        }
                      }}
                    >
                      <Box sx={{ position: 'relative' }}>
                        {navButton}
                        {isSelected && (
                          <Box
                            sx={{
                              position: 'absolute',
                              right: -8,
                              top: '50%',
                              transform: 'translateY(-50%)',
                              width: 4,
                              height: 20,
                              background: item.color,
                              borderRadius: '2px 0 0 2px',
                              boxShadow: `0 0 8px ${item.color}60`
                            }}
                          />
                        )}
                      </Box>
                    </Tooltip>
                  ) : (
                    navButton
                  )}
          </ListItem>
              </Fade>
            );
          })}
      </List>
      </Box>

      {/* Footer */}
      <Box 
        sx={{ 
          p: 2,
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(0, 0, 0, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1
        }}
      >
        <Fade in={!sidebarCollapsed} timeout={300}>
          <Typography 
            variant="caption" 
            sx={{ 
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '0.7rem',
              textAlign: 'center',
              display: 'block'
            }}
          >
            MATLAB Automation Platform v1.0
          </Typography>
        </Fade>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { 
            md: sidebarCollapsed 
              ? `calc(100% - ${collapsedDrawerWidth}px)` 
              : `calc(100% - ${drawerWidth}px)` 
          },
          ml: { 
            md: sidebarCollapsed 
              ? `${collapsedDrawerWidth}px` 
              : `${drawerWidth}px` 
          },
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          boxShadow: '0 4px 20px rgba(25, 118, 210, 0.3)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <Toolbar sx={{ px: 3 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ 
              mr: 2, 
              display: { md: 'none' },
              background: 'rgba(255, 255, 255, 0.1)',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.2)',
              }
            }}
          >
            <MenuIcon />
          </IconButton>
          
          <Box sx={{ flexGrow: 1 }}>
            <Typography 
              variant="h6" 
              noWrap 
              component="div" 
              sx={{ 
                fontWeight: 600,
                color: 'white'
              }}
            >
            MATLAB Automation Platform
          </Typography>
          </Box>
          
          {currentUser && (
            <Box display="flex" alignItems="center" gap={2}>
              <Button
                color="inherit"
                startIcon={<Avatar sx={{ width: 24, height: 24, background: 'rgba(255, 255, 255, 0.2)' }}>
                  {currentUser.username.charAt(0).toUpperCase()}
                </Avatar>}
                onClick={handleMenu}
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '20px',
                  px: 2,
                  py: 1,
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.2)',
                  }
                }}
              >
                {currentUser.username}
              </Button>
              <Menu
                anchorEl={anchorEl}
                open={open}
                onClose={handleMenuClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                PaperProps={{
                  sx: {
                    borderRadius: '12px',
                    mt: 1,
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
                    border: '1px solid rgba(0, 0, 0, 0.05)',
                  }
                }}
              >
                <MenuItem 
                  onClick={() => { navigate('/settings'); handleMenuClose(); }}
                  sx={{ borderRadius: '8px', mx: 1, my: 0.5 }}
                >
                  <ListItemIcon>
                    <AccountCircle fontSize="small" />
                  </ListItemIcon>
                  Account Settings
                </MenuItem>
                <MenuItem 
                  onClick={() => { navigate('/change-password'); handleMenuClose(); }}
                  sx={{ borderRadius: '8px', mx: 1, my: 0.5 }}
                >
                  <ListItemIcon>
                    <Lock fontSize="small" />
                  </ListItemIcon>
                  Change Password
                </MenuItem>
                <MenuItem 
                  onClick={() => { handleLogout(); handleMenuClose(); }}
                  sx={{ borderRadius: '8px', mx: 1, my: 0.5 }}
                >
                  <ListItemIcon>
                    <Logout fontSize="small" />
                  </ListItemIcon>
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ 
          width: { 
            md: sidebarCollapsed ? collapsedDrawerWidth : drawerWidth 
          }, 
          flexShrink: { md: 0 },
          transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        aria-label="navigation"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: sidebarCollapsed ? collapsedDrawerWidth : drawerWidth,
              height: '100vh',
              position: 'relative',
              background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
              transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              overflow: 'hidden',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { 
            md: sidebarCollapsed 
              ? `calc(100% - ${collapsedDrawerWidth}px)` 
              : `calc(100% - ${drawerWidth}px)` 
          },
          height: '100vh',
          overflow: 'auto',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        }}
      >
        <Toolbar />
        <Box 
          sx={{ 
            height: 'calc(100vh - 64px)', 
            overflow: 'auto',
            borderRadius: '16px',
            background: 'white',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            border: '1px solid rgba(0, 0, 0, 0.05)',
          }}
        >
          <Box sx={{ p: 1, height: '100%', boxSizing: 'border-box' }}>
            {children}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
