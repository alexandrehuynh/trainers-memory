import LoginForm from '@/components/auth/LoginForm';
import Navigation from '@/components/Navigation';

export const metadata = {
  title: 'Log In - Trainer\'s Memory',
  description: 'Log in to your Trainer\'s Memory account',
};

export default function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow flex items-center justify-center px-4 py-12">
        <LoginForm />
      </main>
    </div>
  );
} 