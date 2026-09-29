import { useEffect } from 'react';

// The portfolio is a standalone HTML/CSS/JavaScript page. Keep the existing
// React application and its authenticated routes behind the same site.
export default function LandingPage() {
  useEffect(() => {
    window.location.replace('/portfolio/index.html');
  }, []);

  return <a href="/portfolio/index.html">Open Raqeeb</a>;
}
