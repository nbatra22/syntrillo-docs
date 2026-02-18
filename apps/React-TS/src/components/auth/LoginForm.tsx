import React, { useState } from 'react';

interface LoginFormProps {
  onLoginSuccess: () => void;
  onShowForgotPassword: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess, onShowForgotPassword }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleLogin = async () => {
    // TODO: Implement actual login logic with Flask backend
    // For now, just simulate login
    try {
      // const response = await fetch('/auth/login', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ username: email, password })
      // });

      // Temporary: auto-login for development
      localStorage.setItem('authToken', 'temp-token');
      setMessage('Login successful!');
      setTimeout(() => onLoginSuccess(), 500);
    } catch (error) {
      setMessage('Login failed');
    }
  };

  return (
    <div className="w-full max-w-[350px] mx-auto mt-8 bg-white rounded-lg shadow-md p-8 flex flex-col gap-5">
      <div className="text-xl font-bold text-center mb-2">Login</div>

      <div className="flex flex-col gap-1 mb-4">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="p-2 border border-gray-300 rounded-md outline-none text-base bg-gray-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 transition-colors"
          required
        />
      </div>

      <div className="flex flex-col gap-1 mb-4">
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="p-2 border border-gray-300 rounded-md outline-none text-base bg-gray-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 transition-colors"
          required
        />
      </div>

      <button
        onClick={handleLogin}
        className="w-full p-2 text-base text-white rounded-md border-none bg-blue-500 mb-2 transition-all cursor-pointer hover:bg-blue-600"
      >
        Login
      </button>

      <button
        onClick={onShowForgotPassword}
        className="bg-transparent border-none text-blue-500 underline cursor-pointer text-sm mb-2"
      >
        Forgot Password?
      </button>

      {message && (
        <div className={`text-sm min-h-[1.2em] text-center w-full ${message.includes('successful') ? 'text-green-600' : 'text-red-500'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default LoginForm;
