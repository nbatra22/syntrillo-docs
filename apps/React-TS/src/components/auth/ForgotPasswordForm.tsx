import React, { useState } from 'react';

interface ForgotPasswordFormProps {
  onShowLogin: () => void;
  onShowResetPassword: () => void;
}

const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({ onShowLogin, onShowResetPassword }) => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleForgotPassword = async () => {
    // TODO: Implement actual forgot password logic with Flask backend
    try {
      // const response = await fetch('/auth/forgot-password', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ username: email })
      // });

      setMessage('Reset code sent to your email!');
      setTimeout(() => {
        onShowResetPassword();
      }, 2000);
    } catch (error) {
      setMessage('Failed to send reset code');
    }
  };

  return (
    <div className="w-full max-w-[350px] mx-auto mt-8 bg-white rounded-lg shadow-md p-8 flex flex-col gap-5">
      <div className="text-xl font-bold text-center mb-2">Forgot Password</div>

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

      <button
        onClick={handleForgotPassword}
        className="w-full p-2 text-base text-white rounded-md border-none bg-blue-500 mb-2 transition-all cursor-pointer hover:bg-blue-600"
      >
        Send Reset Code
      </button>

      <button
        onClick={onShowLogin}
        className="bg-transparent border-none text-blue-500 underline cursor-pointer text-sm mb-2"
      >
        Back to Login
      </button>

      {message && (
        <div className={`text-sm min-h-[1.2em] text-center w-full ${message.includes('sent') ? 'text-green-600' : 'text-red-500'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default ForgotPasswordForm;
