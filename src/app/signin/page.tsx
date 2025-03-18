import SignInForm from '@/components/auth/SignInForm';

export const metadata = {
  title: 'Sign In - Trainer&apos;s Memory',
  description: 'Sign in to your Trainer&apos;s Memory account',
};

export default function SignInPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow flex items-center justify-center px-4 py-12">
        <SignInForm />
      </main>
    </div>
  );
}