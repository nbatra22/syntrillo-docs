import React, { useState, useEffect } from 'react';
import LoginForm from '../../components/auth/LoginForm';
import ForgotPasswordForm from '../../components/auth/ForgotPasswordForm';
import ResetPasswordForm from '../../components/auth/ResetPasswordForm';
import ProviderSidebar from '../../components/provider-sidebar/ProviderSidebar';

type AuthView = 'login' | 'forgot-password' | 'reset-password' | 'sidebar';

const ProviderSidebarPage: React.FC = () => {
  const [currentView, setCurrentView] = useState<AuthView>('login');
  const [forgotEmail, setForgotEmail] = useState('');

  useEffect(() => {
    // Check if user is already logged in
    const authToken = localStorage.getItem('authToken');
    if (authToken) {
      setCurrentView('sidebar');
    }
  }, []);

  const handleLoginSuccess = () => {
    setCurrentView('sidebar');
  };

  const handleShowForgotPassword = () => {
    setCurrentView('forgot-password');
  };

  const handleShowLogin = () => {
    setCurrentView('login');
  };

  const handleShowResetPassword = () => {
    setCurrentView('reset-password');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === 'login' && (
        <LoginForm
          onLoginSuccess={handleLoginSuccess}
          onShowForgotPassword={handleShowForgotPassword}
        />
      )}

      {currentView === 'forgot-password' && (
        <ForgotPasswordForm
          onShowLogin={handleShowLogin}
          onShowResetPassword={handleShowResetPassword}
        />
      )}

      {currentView === 'reset-password' && (
        <ResetPasswordForm
          onShowLogin={handleShowLogin}
          email={forgotEmail}
        />
      )}

      {currentView === 'sidebar' && <ProviderSidebar />}
    </div>
  );
};

export default ProviderSidebarPage;
