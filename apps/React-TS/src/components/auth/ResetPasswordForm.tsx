import React, { useState } from 'react';

interface ResetPasswordFormProps {
  onShowLogin: () => void;
  email: string;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({ onShowLogin, email }) => {
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleResetPassword = async () => {
    // TODO: Implement actual reset password logic with Flask backend
    try {
      // const response = await fetch('/auth/reset-password', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ username: email, code, new_password: newPassword })
      // });

      setMessage('Password reset successful! Please login.');
      setTimeout(() => {
        onShowLogin();
      }, 2000);
    } catch (error) {
      setMessage('Failed to reset password');
    }
  };

  return (
    <div className="w-full max-w-[350px] mx-auto mt-8 bg-white rounded-lg shadow-md p-8 flex flex-col gap-5">
      <div className="text-xl font-bold text-center mb-2">Reset Password</div>

      <div className="flex flex-col gap-1 mb-4">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Verification Code"
          className="p-2 border border-gray-300 rounded-md outline-none text-base bg-gray-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 transition-colors"
          required
        />
      </div>

      <div className="flex flex-col gap-1 mb-4">
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="New Password"
          className="p-2 border border-gray-300 rounded-md outline-none text-base bg-gray-50 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 transition-colors"
          required
        />
      </div>

      <button
        onClick={handleResetPassword}
        className="w-full p-2 text-base text-white rounded-md border-none bg-blue-500 mb-2 transition-all cursor-pointer hover:bg-blue-600"
      >
        Reset Password
      </button>

      <button
        onClick={onShowLogin}
        className="bg-transparent border-none text-blue-500 underline cursor-pointer text-sm mb-2"
      >
        Back to Login
      </button>

      {message && (
        <div className={`text-sm min-h-[1.2em] text-center w-full ${message.includes('successful') ? 'text-green-600' : 'text-red-500'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default ResetPasswordForm;
