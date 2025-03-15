import { redirect } from "next/navigation";

// This is a catch-all route handler that will handle any unrecognized routes
export default function CatchAllPage({ params }: { params: { slug?: string[] } }) {
  const path = params.slug?.join('/') || '';
  
  // Handle known routes explicitly
  if (path === 'signin') {
    // Serve the signin content directly instead of redirecting
    return (
      <iframe 
        src="/_content/signin" 
        style={{ border: 'none', width: '100%', height: '100vh' }} 
      />
    );
  }
  
  if (path === 'login') {
    // Serve the login content directly instead of redirecting
    return (
      <iframe 
        src="/_content/login" 
        style={{ border: 'none', width: '100%', height: '100vh' }} 
      />
    );
  }
  
  // Fallback to homepage for unknown routes
  return redirect('/');
} 