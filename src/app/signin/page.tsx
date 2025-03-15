import SignInForm from '@/components/auth/SignInForm';
import Navigation from '@/components/Navigation';

export const metadata = {
  title: 'Sign In - Trainer\'s Memory',
  description: 'Sign in to your Trainer\'s Memory account',
};

export default function SignInPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow flex items-center justify-center px-4 py-12">
        <SignInForm />
      </main>
    </div>
  );
}